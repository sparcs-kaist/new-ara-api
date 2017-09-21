from rest_framework import permissions


class VotePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user == obj.created_by
