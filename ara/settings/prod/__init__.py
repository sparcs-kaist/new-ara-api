from datetime import datetime, timezone

from ara.settings import MIDDLEWARE, REST_FRAMEWORK
from ara.settings import OTL_API_BASE_URL as _OTL_BASE_URL_FROM_ENV

DEBUG = False

ALLOWED_HOSTS = [
    "newara.sparcs.org",
    "newara-api.sparcs.org",
    "ara.sparcs.org",
]

CSRF_TRUSTED_ORIGINS = [
    "https://newara.sparcs.org",
    "https://newara-api.sparcs.org",
    "https://ara.sparcs.org",
]

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"

MIDDLEWARE += [
    "django.middleware.csrf.CsrfViewMiddleware",
]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.BasicAuthentication",
    "rest_framework.authentication.SessionAuthentication",
    "ara.authentication.OneAppJWTAuthentication", #OneApp전용 JWT 인증 Class
)

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 20
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)

# env 가 명시적으로 set 됐으면 그걸 우선, 아니면 prod 기본 OTL endpoint
OTL_API_BASE_URL = _OTL_BASE_URL_FROM_ENV or "https://otl.sparcs.org/api"
