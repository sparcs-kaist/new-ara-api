"""과목 누적 게시판 그룹 정책 계산과 기존 데이터 재배치."""

from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction

from apps.course.models import CourseGroupingRule

# CourseGroup.professors_key는 기본 정책에서는 실제 교수 집합 키다. 관리자가
# COURSE_CODE 전략을 선택한 과목에서는 모든 교수 집합이 이 예약 키를 공유한다.
COURSE_CODE_GROUP_KEY = "__course_code__"


def normalize_course_code(course_code: str) -> str:
    return course_code.strip().upper()


def grouping_key_for(
    professors_key: str,
    strategy: str | None = None,
) -> str:
    """관리자 전략을 실제 CourseGroup 식별 키로 변환."""
    if strategy == CourseGroupingRule.Strategy.COURSE_CODE:
        return COURSE_CODE_GROUP_KEY
    return professors_key


def active_grouping_strategies(course_codes: Iterable[str]) -> dict[str, str]:
    """OTL payload의 과목들에 적용할 활성 규칙을 한 번의 쿼리로 조회."""
    normalized_codes = {normalize_course_code(code) for code in course_codes}
    return {
        normalize_course_code(rule.course_code): rule.strategy
        for rule in CourseGroupingRule.objects.filter(
            course_code__in=normalized_codes,
            is_active=True,
        ).only("course_code", "strategy")
    }


@transaction.atomic
def regroup_existing_courses(course_code: str) -> None:
    """규칙 변경 직후 기존 Course와 Article을 새 그룹 정책에 맞춰 재연결.

    Article은 작성 당시 진입점인 related_course를 보존하므로, 그 Course가 새로
    선택한 group으로 related_course_group을 함께 옮길 수 있다. 사용되지 않게 된
    CourseGroup은 이력과 안전한 롤백을 위해 삭제하지 않는다.
    """
    from apps.core.models import Article
    from apps.course.models import Course, CourseGroup

    normalized_code = normalize_course_code(course_code)
    rule = (
        CourseGroupingRule.objects.filter(
            course_code=normalized_code,
            is_active=True,
        )
        .only("strategy")
        .first()
    )
    strategy = rule.strategy if rule is not None else None

    courses = Course.objects.filter(course_code__iexact=normalized_code).order_by(
        "-year", "-semester", "id"
    )
    for course in courses:
        group_key = grouping_key_for(course.professors_key, strategy)
        group, created = CourseGroup.objects.get_or_create(
            course_code=course.course_code,
            professors_key=group_key,
            defaults={
                "title": course.title,
                "title_year": course.year,
                "title_semester": course.semester,
            },
        )
        if not created and (course.year, course.semester) > group.title_term():
            group.title = course.title
            group.title_year = course.year
            group.title_semester = course.semester
            group.save(update_fields=["title", "title_year", "title_semester"])

        if course.group_id != group.id:
            Course.objects.filter(pk=course.pk).update(group=group)
        Article.objects.filter(related_course_id=course.pk).exclude(
            related_course_group_id=group.id
        ).update(related_course_group=group)
