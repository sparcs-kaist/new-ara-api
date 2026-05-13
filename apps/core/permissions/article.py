from rest_framework import permissions

from apps.core.models import Article
from apps.core.models.board import BoardAccessPermissionType


class ArticlePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.created_by
        return super().has_object_permission(request, view, obj)


class ArticleReadPermission(permissions.BasePermission):
    message = "해당 게시물에 대한 읽기 권한이 없습니다."

    def has_object_permission(self, request, view, obj: Article):
        return obj.parent_board.group_has_access_permission(
            BoardAccessPermissionType.READ, request.user.profile.group
        )

class ArticleModifyPermission(permissions.BasePermission):
    message = "게시글 수정은 작성자 본인만 가능합니다"

    def has_object_permission(self, request, view, obj: Article):
        return obj.parent_board.group_has_access_permission(
            BoardAccessPermissionType.WRITE, request.user.profile.group
        ) and (request.user == obj.created_by)


class ArticleAccessPermission(permissions.BasePermission):
    """과목글이면 enrollment 체크, 아니면 board read mask.

    /api/articles/<id>/vote_*/ 등 detail 액션에서 사용. retrieve 는 기존
    ArticleReadPermission (board mask only) 가 그대로 dummy board (mask=0)
    로 차단하도록 두고, vote/scrap/report 같은 행위는 enrollment 로 통과시킨다.
    """

    message = "해당 게시물에 대한 접근 권한이 없습니다."

    def has_object_permission(self, request, view, obj: Article):
        from apps.course.access import can_read_article as course_can_read
        from apps.major.access import can_read_article as major_can_read
        from apps.major.access import is_major_article

        if is_major_article(obj):
            return major_can_read(request.user, obj)
        return course_can_read(request.user, obj)