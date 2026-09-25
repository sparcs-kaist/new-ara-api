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
            # "false" 같은 문자열로 와도 저장되게
            is_web = request.data.get("is_web", True)
            if isinstance(is_web, str):
                is_web = is_web.lower() in ("true", "1")
            token = FCMToken(
                token=token,
                user=request.user,
                last_activated_at=Now(),
                is_web=is_web,
            )
            token.save()
        return Response(status=status.HTTP_200_OK)
