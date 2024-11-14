import socket
from datetime import datetime, timezone

import pymysql

from ara.settings import INSTALLED_APPS, LOGGING, MIDDLEWARE

from ..djangorestframework import REST_FRAMEWORK

pymysql.install_as_MySQLdb()

DEBUG = True

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "https://*.sparcs.org",
    "http://localhost",
]

CORS_ALLOW_ALL_ORIGINS = True

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
)

LOGGING["disable_existing_loggers"] = False

REPORT_THRESHOLD = 4
SCHOOL_RESPONSE_VOTE_THRESHOLD = 3
ANSWER_PERIOD = 14
MIN_TIME = datetime.min.replace(tzinfo=timezone.utc)
