from rest_framework import permissions


class BlockPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return super().has_object_permission(request, view, obj) and (
            request.user.is_staff or request.user == obj.blocked_by
        )
