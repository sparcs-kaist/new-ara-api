from typing import TypeVar

from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = TypeVar("User", bound=get_user_model())


class LoggedInUserRequest(HttpRequest):
    user: User
