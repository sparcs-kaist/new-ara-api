from rest_framework import permissions

from apps.user.models import UserProfile


class CommunicationArticleAdminPermission(permissions.IsAuthenticated):
    message = "You are not authorized to access this feature"

    def has_permission(self, request, view):
        return request.user.is_staff or request.user.profile.has_group_by_id(
            7
        )  # 7 = Communication board admin
