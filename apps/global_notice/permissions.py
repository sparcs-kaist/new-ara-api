from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsGlobalNoticeAthenticated(permissions.IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if request.method not in permissions.SAFE_METHODS:
            return request.user.is_staff or request.user.is_superuser

        # SAFE_METHODS는 비로그인 허용
        return True


class GlobalNoticePermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return super().has_permission(request, view)
