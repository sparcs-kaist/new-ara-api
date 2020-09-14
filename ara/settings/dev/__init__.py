from ara.settings import INSTALLED_APPS, MIDDLEWARE
from ..djangorestframework import REST_FRAMEWORK

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = 'None'

INSTALLED_APPS += [
    'corsheaders',
    'debug_toolbar',
]

MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.BasicAuthentication',
    'ara.authentication.CsrfExemptSessionAuthentication',
)


try:
    from .local_settings import *
except ImportError:
    pass
