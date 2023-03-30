from rest_framework import permissions


class UserProfilePermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.method == "GET":
            return super().has_object_permission(request, view, obj)
        else:
            return request.user.is_staff or request.user == obj.user
