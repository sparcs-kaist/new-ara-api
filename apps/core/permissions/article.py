from rest_framework import permissions

from apps.core.models import Article


class ArticlePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.created_by

        return super().has_object_permission(request, view, obj)


# TODO: Rename to ArticleGroupPermission
class ArticleKAISTPermission(permissions.BasePermission):
    message = 'KAIST 구성원만 읽을 수 있는 게시물입니다.'

    def has_object_permission(self, request, view, obj: Article):
        return obj.parent_board.group_has_access(request.user.profile.group)
