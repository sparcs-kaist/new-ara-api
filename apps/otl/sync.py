"""OTL → Ara 동기화 로직.

호출 시점: 유저가 `/api/courses/me/` 부를 때 (lazy, on-demand).
- 24시간 캐시: 가장 최근 enrollment.last_seen_in_otl_at 가 24h 안이면 skip.
- 응답 = 진실의 source. 응답에 없는 enrollment 는 hard-delete (드랍 1일 내 반영).
- 끝난 학기 takenLecture 는 OTL 이 보관하므로 자동으로 영구 보존됨.
- OTL 다운: OtlSyncError 발생, 호출자가 stale fallback.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import timedelta
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from apps.course.models import Course, CourseEnrollment, Professor
from apps.otl import client
from apps.otl.client import OtlApiError, OtlAuthError

log = logging.getLogger(__name__)

SYNC_TTL = timedelta(hours=24)


class OtlSyncError(Exception):
    """sync 가 실패해서 OTL 데이터를 반영하지 못함. 호출자가 stale 로 fallback."""


def is_user_enrollment_fresh(user) -> bool:
    latest = (
        CourseEnrollment.objects
        .filter(user=user)
        .order_by("-last_seen_in_otl_at")
        .values_list("last_seen_in_otl_at", flat=True)
        .first()
    )
    if latest is None:
        return False
    return (timezone.now() - latest) < SYNC_TTL


def sync_user_courses(user, *, force: bool = False) -> None:
    """OTL 에서 user 의 takenLecture 받아서 Course/Enrollment 갱신.

    force=False 이고 24h 안에 sync 한 적 있으면 OTL 호출 없이 바로 return.
    """
    if not force and is_user_enrollment_fresh(user):
        return

    profile = user.profile
    if not profile.uid:
        raise OtlSyncError(f"user {user.id} has no sparcs uid")

    try:
        otl_user_id = _ensure_otl_user_id(profile)
        payload = client.get_user_lectures(profile.uid, otl_user_id)
    except OtlAuthError as e:
        # uid 매핑이 깨진 경우 — 캐시된 otl_user_id 가 남아있다면 한 번 재시도
        if profile.otl_user_id is not None:
            log.warning("OTL auth failed with cached user_id; refetching info: %r", e)
            profile.otl_user_id = None
            profile.save(update_fields=["otl_user_id"])
            otl_user_id = _ensure_otl_user_id(profile)
            payload = client.get_user_lectures(profile.uid, otl_user_id)
        else:
            raise OtlSyncError(f"OTL auth rejected: {e}") from e
    except OtlApiError as e:
        raise OtlSyncError(f"OTL fetch failed: {e}") from e

    new_course_ids = _apply_sync_payload(user, payload)

    # 학점/학과는 takenLectures 응답에 없어 별도 호출 필요. 새로 생긴 Course 만 1회.
    if new_course_ids:
        _enrich_new_courses(profile.uid, new_course_ids)


def _ensure_otl_user_id(profile) -> int:
    if profile.otl_user_id:
        return profile.otl_user_id
    info = client.get_user_info(profile.uid)
    otl_uid = info.get("id") if info else None
    if not isinstance(otl_uid, int):
        raise OtlSyncError(f"OTL /info missing numeric id: {info!r}")
    profile.otl_user_id = otl_uid
    profile.save(update_fields=["otl_user_id"])
    return otl_uid


def _apply_sync_payload(user, payload: dict) -> list[int]:
    """OTL 응답을 정규화해서 Course / Enrollment row 갱신.

    같은 (year, semester, course_code, prof_set) 분반들은 한 Course 로 합본.
    Returns: 이번 sync 에서 새로 생성된 Course id 리스트 (학점/학과 enrich 대상).
    """
    now = timezone.now()
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    prof_pool: dict[int, str] = {}

    for wrap in payload.get("lecturesWrap", []) or []:
        year = wrap.get("year")
        semester = wrap.get("semester")
        if year is None or semester is None:
            continue
        for lec in wrap.get("lectures", []) or []:
            profs = sorted(lec.get("professors") or [], key=lambda p: p["id"])
            for p in profs:
                prof_pool[p["id"]] = p["name"]
            key = ",".join(str(p["id"]) for p in profs)
            grouped[(year, semester, lec["code"], key)].append({
                "name": lec["name"],
                "courseId": lec["courseId"],
                "lectureId": lec["lectureId"],
                "prof_ids": [p["id"] for p in profs],
            })

    new_course_ids: list[int] = []
    course_ids: list[int] = []

    with transaction.atomic():
        # Professor upsert (이름 갱신 포함)
        for pid, name in prof_pool.items():
            Professor.objects.update_or_create(id=pid, defaults={"name": name})

        # Course upsert
        for (year, semester, code, key), lectures in grouped.items():
            first = lectures[0]
            otl_lecture_ids = sorted({lec["lectureId"] for lec in lectures})
            course, created = Course.objects.update_or_create(
                course_code=code,
                year=year,
                semester=semester,
                professors_key=key,
                defaults={
                    "title": first["name"],
                    "otl_course_id": first["courseId"],
                    "otl_lecture_ids": otl_lecture_ids,
                },
            )
            course.professors.set(first["prof_ids"])
            course_ids.append(course.id)
            if created:
                new_course_ids.append(course.id)

        # Enrollment 갱신: 새 row 추가 + 기존 row 의 last_seen 갱신
        existing = set(
            CourseEnrollment.objects.filter(user=user).values_list("course_id", flat=True)
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

        # 응답에 안 보이는 enrollment 는 hard-delete (드랍 처리)
        CourseEnrollment.objects.filter(user=user).exclude(
            course_id__in=course_ids
        ).delete()

    return new_course_ids


def _enrich_new_courses(uid: str, course_ids: Iterable[int]) -> None:
    """학점/학과 정보 채우기 (best-effort, 실패해도 무시)."""
    courses = Course.objects.filter(id__in=list(course_ids)).only(
        "id", "otl_course_id"
    )
    for course in courses:
        try:
            detail = client.get_course_detail(uid, course.otl_course_id)
        except OtlApiError as e:
            log.warning(
                "OTL course detail enrich failed (course_id=%s): %r", course.id, e
            )
            continue
        if not detail:
            continue
        Course.objects.filter(pk=course.pk).update(
            credit=detail.get("credit"),
            department_name=(
                (detail.get("department") or {}).get("name") or ""
            )[:64],
        )
