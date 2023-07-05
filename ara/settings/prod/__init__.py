from datetime import datetime, timezone

from ara.settings import MIDDLEWARE, REST_FRAMEWORK

DEBUG = False

ALLOWED_HOSTS = [
    "newara.sparcs.org",
    "ara.sparcs.org",
]

CSRF_TRUSTED_ORIGINS = [
    "newara.sparcs.org",
    "ara.sparcs.org",
]

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"

MIDDLEWARE += [
    "django.middleware.csrf.CsrfViewMiddleware",
]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.SessionAuthentication",
)

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 20
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)
