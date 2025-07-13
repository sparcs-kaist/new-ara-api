from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

#for OneApp
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from apps.user.models import UserProfile


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class JWTCookieAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. 쿠키에서 access 토큰을 찾음
        raw_token = request.COOKIES.get("access")

        # 2. 없으면 헤더에서 찾음 (Authorization: Bearer ...)
        if not raw_token:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception:
            # 예외 발생 시 None 반환, 세션 인증으로 넘어가게 함
            return None

        return self.get_user(validated_token), validated_token

class OneAppJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, settings.ONE_APP_JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid JWT token')

        uid = payload.get('uid')
        if not uid:
            raise exceptions.AuthenticationFailed('UID missing in token')

        try:
            profile = UserProfile.objects.get(uid=uid)
            user = profile.user
        except UserProfile.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, None)