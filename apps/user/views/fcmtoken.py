from django.db.models.functions import Now
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import FCMToken


class FCMTokenView(APIView):
    def patch(self, request, mode):
        token = request.data["token"]
        if mode == "delete":
            FCMToken.objects.filter(token=token).delete()
            pass
        elif mode == "update":
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            token = FCMToken(token=token, user=request.user, last_activated_at=Now())
            token.save()
        return Response(status=status.HTTP_200_OK)
