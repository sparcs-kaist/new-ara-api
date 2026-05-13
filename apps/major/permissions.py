from rest_framework import permissions

# Read = Auth and Write = Auth + only thier major.
class ReadAuthWriteOwnMajor(permissions.BasePermission):
    """
    Allow read-only access to any user, but only allow write access to their own major.

    ViewSet 의 view-level + object-level 권한 체크.
    - 인증 필수.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the major.
        return obj.major_id == request.user.sso_user_info.kaist_v2_info.get("std_dep_id")
    

