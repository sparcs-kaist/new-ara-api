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
