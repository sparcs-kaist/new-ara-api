from rest_framework import permissions


class CommunicationArticleAdminPermission(permissions.IsAuthenticated):
    message = "You are not authorized to access this feature"

    def has_permission(self, request, view):
        return request.user.is_staff or request.user.profile.is_school_admin
