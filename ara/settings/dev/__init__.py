from ara.settings import INSTALLED_APPS, MIDDLEWARE

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
