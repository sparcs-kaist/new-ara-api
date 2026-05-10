"""과목게시판 권한.

룰: 해당 Course 에 CourseEnrollment 가 있는 user 만 read/write 가능.
끝난 학기 enrollment 도 OTL 이 보관해주는 한 그대로 남으므로 영구 read 가
자연스럽게 유지된다 (별도 만료 룰 없음).
"""

from __future__ import annotations

from rest_framework import permissions

from apps.course.models import CourseEnrollment


class IsEnrolledInCourse(permissions.BasePermission):
    """ViewSet 의 view-level + object-level 권한 체크.

    - URL kwarg `course_id` 또는 `pk` (CourseViewSet) 로부터 course 식별.
    - 인증 필수.
    """

    message = "해당 과목 게시판에 접근할 권한이 없습니다."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        course_id = view.kwargs.get("course_id") or view.kwargs.get("pk")
        if course_id is None:
            # list/me 등 course 가 특정되지 않는 액션은 viewset 의 get_queryset 이
            # enrollment 로 필터링하므로 통과.
            return True

        return CourseEnrollment.objects.filter(
            user=request.user, course_id=course_id
        ).exists()

    def has_object_permission(self, request, view, obj) -> bool:
        # obj 는 Course 또는 Article (related_course FK)
        course_id = getattr(obj, "id", None)
        if hasattr(obj, "related_course_id"):
            course_id = obj.related_course_id
        if course_id is None:
            return False
        return CourseEnrollment.objects.filter(
            user=request.user, course_id=course_id
        ).exists()
