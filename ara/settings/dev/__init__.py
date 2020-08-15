from ara.settings import INSTALLED_APPS, MIDDLEWARE
from ..djangorestframework import *

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True

SSO_IS_BETA = False

INSTALLED_APPS += [
    'silk',
    'debug_toolbar',
]

MIDDLEWARE += [
    'silk.middleware.SilkyMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.SessionAuthentication',
    'rest_framework.authentication.BasicAuthentication',
)