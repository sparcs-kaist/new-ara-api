import socket
from datetime import datetime, timezone

from ara.settings import INSTALLED_APPS, LOGGING, MIDDLEWARE

from ..djangorestframework import REST_FRAMEWORK

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True
ALLOWED_HOSTS = ["*"]

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "https://sparcs.org",
    "https://*.sparcs.org",  # 모든 하위 도메인 허용
]

INSTALLED_APPS += [
    "corsheaders",
    "debug_toolbar",
]

MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "debug_toolbar_force.middleware.ForceDebugToolbarMiddleware",
]

# https://django-debug-toolbar.readthedocs.io/

_, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + [
    "127.0.0.1",
    "10.0.2.2",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda _: True,
}

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.BasicAuthentication",
    "ara.authentication.CsrfExemptSessionAuthentication",
    "ara.authentication.JWTCookieAuthentication",
)

LOGGING["disable_existing_loggers"] = False

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 3
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)
