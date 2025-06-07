from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


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
