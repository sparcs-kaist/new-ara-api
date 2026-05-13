"""학과게시판 권한.

룰: 본인의 학과 (sso_user_info.kaist_v2_info.std_dept_id) 에 해당하는
Major 게시판만 read/write 가능. course 의 IsEnrolledInCourse 와 동일한
구조 (view-level + object-level).
"""

from __future__ import annotations

from rest_framework import permissions

from apps.major.access import _is_same_major


class IsSameMajor(permissions.BasePermission):
    """ViewSet 의 view-level + object-level 권한 체크.

    - URL kwarg `major_id` (Major PK) 로부터 major 식별.
    - 인증 필수.
    - 학과별 게시판은 same-major 만 read/write 가능.
    """

    message = "해당 학과 게시판에 접근할 권한이 없습니다."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        major_pk = view.kwargs.get("major_id") or view.kwargs.get("pk")
        if major_pk is None:
            # list/me 등 major 가 특정되지 않는 액션은 viewset 의
            # get_queryset 이 필터링하므로 통과.
            return True

        return _is_same_major(request.user, int(major_pk))

    def has_object_permission(self, request, view, obj) -> bool:
        # obj 는 Major 또는 Article (related_major FK)
        major_pk = getattr(obj, "id", None)
        if hasattr(obj, "related_major_id"):
            major_pk = obj.related_major_id
        if major_pk is None:
            return False
        return _is_same_major(request.user, major_pk)
