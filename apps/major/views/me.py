from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.user_profile import UserProfile
from apps.user.serializers.user_profile import MyPageUserProfileSerializer


class MeView(APIView):
    """
    Get the SSO_user_info which contains the user's major. 
    """

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            profile = UserProfile.objects.get(user_id=request.user.id)
        except UserProfile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(profile.sso_user_info, status=status.HTTP_200_OK)
