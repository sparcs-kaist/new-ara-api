from rest_framework import permissions

from apps.core.models import Article


class ArticlePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.created_by
        return super().has_object_permission(request, view, obj)


class ArticleReadPermission(permissions.BasePermission):
    message = "해당 게시물에 대한 읽기 권한이 없습니다."

    def has_object_permission(self, request, view, obj: Article):
        return obj.parent_board.permission_list_by_user(request.user).READ
