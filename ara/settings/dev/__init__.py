from datetime import datetime, timezone

from ara.settings import INSTALLED_APPS, LOGGING, MIDDLEWARE

from ..djangorestframework import REST_FRAMEWORK

DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = ["*"]

CORS_ORIGIN_ALLOW_ALL = True

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = "None"

INSTALLED_APPS += [
    "corsheaders",
    "debug_toolbar",
]

MIDDLEWARE += [
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "debug_toolbar_force.middleware.ForceDebugToolbarMiddleware",
]

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (
    "rest_framework.authentication.BasicAuthentication",
    "ara.authentication.CsrfExemptSessionAuthentication",
)

LOGGING["disable_existing_loggers"] = False

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 3
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)

try:
    from .local_settings import *
except ImportError:
    pass
