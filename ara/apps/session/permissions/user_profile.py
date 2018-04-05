from rest_framework import permissions


class UserProfilePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user == obj.user
