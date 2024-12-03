from typing import Any

from django.http import HttpRequest
from ninja.security import HttpBearer
from rest_framework.authentication import SessionAuthentication


class AuthLoggedInUser(HttpBearer):
    def __call__(self, request: HttpRequest) -> Any | None:
        headers = request.headers
        auth_value = headers.get(self.header)
        if not auth_value:
            return None
        parts = auth_value.split(" ")

        if parts[0].lower() != self.openapi_scheme:
            return None
        return self.authenticate(request)

    def authenticate(self, request: HttpRequest, token: str) -> bool:
        result = SessionAuthentication().authenticate(request)
        if result is None:
            return False
        (user, _) = result
        request.user = user

        return bool(user and user.is_authenticated)
