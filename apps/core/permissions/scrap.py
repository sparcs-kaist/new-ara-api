from rest_framework import permissions


class ScrapPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.scrapped_by

        return super(
            ScrapPermission,
            self).has_object_permission(
            request,
            view,
            obj)
