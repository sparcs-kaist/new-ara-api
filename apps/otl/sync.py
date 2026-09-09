"""OTL → Ara 동기화 로직.

호출 시점: 유저가 `/api/courses/me/?year=&semester=` 호출 시 (lazy, per-term).
- (year, semester) 단위 sync. my-timetable 한 번이면 끝.
- 캐시: current 와 직전 학기까지는 24h TTL, current-2 학기부터는 ∞ 캐시.
  KAIST 학사일정 / 계절학기 (2, 4) 경계가 들쭉날쭉이라 한 학기 margin.
- 응답 = 진실의 source. 응답에 없는 enrollment 는 해당 (year, semester) 안에서만 soft-delete.
- OTL 다운: OtlSyncError 발생, 호출자가 stale fallback.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Tuple

from django.db import transaction
from django.utils import timezone

from apps.course.grouping import (
    active_grouping_strategies,
    grouping_key_for,
    normalize_course_code,
)
from apps.course.models import Course, CourseEnrollment, CourseGroup, Professor
from apps.otl import client
from apps.otl.client import OtlApiError, OtlAuthError

log = logging.getLogger(__name__)

SYNC_TTL = timedelta(hours=24)


class OtlSyncError(Exception):
    """sync 가 실패해서 OTL 데이터를 반영하지 못함. 호출자가 stale 로 fallback."""


def current_term() -> Tuple[int, int]:
    """현재 날짜로 regular term `(year, semester)`을 추정한다.
    January–July는 spring, August–December는 fall로 처리한다."""
    now = timezone.now()
    y, m = now.year, now.month
    if m <= 7:
        return (y, 1)
    return (y, 3)


def _previous_term(year: int, semester: int) -> Tuple[int, int]:
    if semester == 1:
        return (year - 1, 4)
    return (year, semester - 1)


def is_past_term(year: int, semester: int) -> bool:
    """Current term의 previous term보다 오래된 term인지 확인한다.
    이 margin은 term boundary 오차가 permanent cache로 남는 것을 방지한다."""
    cy, cs = current_term()
    return (year, semester) < _previous_term(cy, cs)


def _term_enrollment_qs(user, year: int, semester: int):
    return CourseEnrollment.objects.filter(
        user=user, course__year=year, course__semester=semester
    )


def is_term_cache_fresh(user, year: int, semester: int) -> bool:
    qs = _term_enrollment_qs(user, year, semester)
    if is_past_term(year, semester):
        # 과거 학기: 1건이라도 있으면 영구 캐시. 0건이면 한 번 더 시도 (신규 유저 등).
        return qs.exists()
    # 현재/미래 학기: 가장 최근 last_seen 이 24h 안쪽이면 fresh.
    latest = (
        qs.order_by("-last_seen_in_otl_at")
        .values_list("last_seen_in_otl_at", flat=True)
        .first()
    )
    if latest is None:
        return False
    return (timezone.now() - latest) < SYNC_TTL


def sync_user_courses(user, year: int, semester: int, *, force: bool = False) -> None:
    """OTL `my-timetable`에서 지정 term의 enrollment를 sync한다."""
    log.info(
        "sync_user_courses start: user=%s year=%s semester=%s force=%s",
        user.id, year, semester, force,
    )

    if not force and is_term_cache_fresh(user, year, semester):
        log.info(
            "sync_user_courses skip: user=%s year=%s semester=%s cache fresh",
            user.id, year, semester,
        )
        return

    profile = user.profile
    if not profile.uid:
        log.warning("sync_user_courses abort: user=%s missing sparcs uid", user.id)
        raise OtlSyncError(f"user {user.id} has no sparcs uid")

    try:
        payload = client.get_my_timetable(profile.uid, year, semester)
    except OtlAuthError as e:
        log.warning("OTL auth rejected (user=%s): %r", user.id, e)
        raise OtlSyncError(f"OTL auth rejected: {e}") from e
    except OtlApiError as e:
        log.warning("OTL fetch failed (user=%s): %r", user.id, e)
        raise OtlSyncError(f"OTL fetch failed: {e}") from e

    _apply_my_timetable(user, year, semester, payload)
    log.info(
        "sync_user_courses done: user=%s year=%s semester=%s", user.id, year, semester,
    )


def _apply_my_timetable(user, year: int, semester: int, payload: dict) -> None:
    """`my-timetable` payload로 `Course`, `Professor`, `Enrollment`를 update한다.
    같은 `(year, semester, code, professors)` lectures는 한 `Course` row로 merge한다."""
    if not isinstance(payload, dict) or "lectures" not in payload:
        raise OtlSyncError(
            f"OTL my-timetable missing 'lectures' key: keys="
            f"{list(payload) if isinstance(payload, dict) else type(payload).__name__}"
        )
    lectures = payload.get("lectures")
    if not isinstance(lectures, list):
        raise OtlSyncError(
            f"OTL my-timetable 'lectures' not a list: {type(lectures).__name__}"
        )

    # Empty payload가 기존 enrollment를 삭제하지 않도록 partial outage를 guard한다.
    if not lectures:
        existing_count = _term_enrollment_qs(user, year, semester).count()
        if existing_count > 0:
            log.warning(
                "OTL my-timetable returned empty lectures but user=%s has %d "
                "enrollments in (%s, %s) — refusing to wipe",
                user.id, existing_count, year, semester,
            )
            raise OtlSyncError(
                f"OTL returned empty lectures for user with {existing_count} "
                f"existing enrollments in ({year}, {semester})"
            )
        log.info(
            "OTL my-timetable empty (user=%s year=%s semester=%s, no existing — no-op)",
            user.id, year, semester,
        )

    now = timezone.now()
    grouped: dict[tuple, list[dict]] = {}
    prof_pool: dict[int, str] = {}

    for lec in lectures:
        code = lec.get("code")
        if not code:
            continue
        profs = sorted(lec.get("professors") or [], key=lambda p: p["id"])
        for p in profs:
            prof_pool[p["id"]] = p["name"]
        prof_key = ",".join(str(p["id"]) for p in profs)
        grouped.setdefault((code, prof_key), []).append({
            "name": lec["name"],
            "courseId": lec["courseId"],
            "lectureId": lec["id"],
            "credit": lec.get("credit"),
            "department_name": ((lec.get("department") or {}).get("name") or "")[:64],
            "prof_ids": [p["id"] for p in profs],
        })

    log.info(
        "OTL payload parsed: user=%s year=%s semester=%s lectures=%d "
        "courses_grouped=%d professors=%d",
        user.id, year, semester, len(lectures), len(grouped), len(prof_pool),
    )

    course_ids: list[int] = []
    new_course_ids: list[int] = []
    grouping_strategies = active_grouping_strategies(
        code for code, _prof_key in grouped
    )

    with transaction.atomic():
        for pid, name in prof_pool.items():
            Professor.objects.update_or_create(id=pid, defaults={"name": name})

        for (code, prof_key), entries in grouped.items():
            first = entries[0]
            otl_lecture_ids = sorted({e["lectureId"] for e in entries})
            # Grouping strategy로 term-independent group을 선택하고 latest term title만 유지한다.
            # Past-term sync가 shared group title을 rollback하지 않도록 newer term에서만 update한다.
            strategy = grouping_strategies.get(normalize_course_code(code))
            group_key = grouping_key_for(prof_key, strategy)
            group, group_created = CourseGroup.objects.get_or_create(
                course_code=code,
                professors_key=group_key,
                defaults={
                    "title": first["name"],
                    "title_year": year,
                    "title_semester": semester,
                },
            )
            if not group_created and (year, semester) > group.title_term():
                group.title = first["name"]
                group.title_year = year
                group.title_semester = semester
                group.save(
                    update_fields=["title", "title_year", "title_semester"]
                )
            course, created = Course.objects.update_or_create(
                course_code=code,
                year=year,
                semester=semester,
                professors_key=prof_key,
                defaults={
                    "title": first["name"],
                    "otl_course_id": first["courseId"],
                    "otl_lecture_ids": otl_lecture_ids,
                    "credit": first["credit"],
                    "department_name": first["department_name"],
                    "group": group,
                },
            )
            course.professors.set(first["prof_ids"])
            course_ids.append(course.id)
            if created:
                new_course_ids.append(course.id)

        existing = set(
            _term_enrollment_qs(user, year, semester).values_list("course_id", flat=True)
        )
        to_create = [
            CourseEnrollment(user=user, course_id=cid, last_seen_in_otl_at=now)
            for cid in course_ids
            if cid not in existing
        ]
        if to_create:
            CourseEnrollment.objects.bulk_create(to_create, ignore_conflicts=True)
        if course_ids:
            CourseEnrollment.objects.filter(
                user=user, course_id__in=course_ids
            ).update(last_seen_in_otl_at=now)

        # 이 (year, semester) 안에서, 응답에 없는 enrollment 만 soft-delete.
        # 다른 학기 enrollment 는 절대 건드리지 않는다.
        stale = _term_enrollment_qs(user, year, semester).exclude(
            course_id__in=course_ids
        )
        stale_count = stale.count()
        if stale_count:
            stale.delete()

    log.info(
        "OTL sync persisted: user=%s year=%s semester=%s total=%d new=%d dropped=%d",
        user.id, year, semester, len(course_ids), len(new_course_ids), stale_count,
    )
