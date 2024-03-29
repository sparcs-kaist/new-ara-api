from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models.user_profile import UserProfile
from apps.user.serializers.user_profile import MyPageUserProfileSerializer


class MeView(APIView):
    """
    Get my information from token
    """

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = MyPageUserProfileSerializer(
            UserProfile.objects.get(user_id=request.user.id)
        )
        return Response(serializer.data)
