from rest_framework import permissions


class ReportPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user == obj.reported_by

        return super(ReportPermission, self).has_object_permission(
            request,
            view,
            obj
        )
