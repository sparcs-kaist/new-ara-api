from rest_framework import permissions


class ArticlePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.created_by

        return super().has_object_permission(request, view, obj)
