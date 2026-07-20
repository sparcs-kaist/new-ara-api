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

    - URL kwarg `std_dept_id` (Major PK) 로부터 major 식별.
    - 인증 필수.
    - 학과별 게시판은 same-major 만 read/write 가능.
    """

    message = "해당 학과 게시판에 접근할 권한이 없습니다."

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        std_dept_id = view.kwargs.get("std_dept_id")
        if std_dept_id is None:
            # list/me 등 major 가 특정되지 않는 액션은 viewset 의
            # get_queryset 이 필터링하므로 통과.
            return True

        return _is_same_major(request.user, std_dept_id)

    def has_object_permission(self, request, view, obj) -> bool:
        # obj 는 Article (related_major FK, = std_dept_id) 또는 Major (PK = std_dept_id).
        if hasattr(obj, "related_major_id"):
            std_dept_id = obj.related_major_id
        else:
            std_dept_id = getattr(obj, "pk", None)
        if std_dept_id is None:
            return False
        return _is_same_major(request.user, std_dept_id)
