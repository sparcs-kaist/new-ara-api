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