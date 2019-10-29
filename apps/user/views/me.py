from rest_framework.views import APIView
from rest_framework.response import Response

from apps.user.models.user_profile import UserProfile
from apps.user.permissions.user_profile import UserProfilePermission
from apps.user.serializers.user_profile import UserProfileSerializer


class MeView(APIView):
    """
    Get my information from token
    """
    permission_classes = (
        UserProfilePermission,
    )

    def get(self, request):
        serializer = UserProfileSerializer(UserProfile.objects.get(user_id=request.user.id))
        return Response(serializer.data)
