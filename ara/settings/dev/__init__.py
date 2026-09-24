import socket
from datetime import datetime, timezone

from ara.settings import INSTALLED_APPS, LOGGING, MIDDLEWARE
from ara.settings import OTL_API_BASE_URL as _OTL_BASE_URL_FROM_ENV

from ..djangorestframework import REST_FRAMEWORK

DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "https://*.sparcs.org",
    "https://*.dev.sparcs.org",
    "http://localhost",
]

CORS_ALLOW_ALL_ORIGINS = True

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = True

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
    "ara.authentication.OneAppJWTAuthentication", #OneApp전용 JWT 인증 Class
)

LOGGING["disable_existing_loggers"] = False

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 3
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)

# env 가 명시적으로 set 됐으면 그걸 우선, 아니면 dev 기본 OTL endpoint
OTL_API_BASE_URL = _OTL_BASE_URL_FROM_ENV or "https://api.otl.dev.sparcs.org"
