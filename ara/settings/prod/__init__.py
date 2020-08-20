from ara.settings import MIDDLEWARE

DEBUG = False

ALLOWED_HOSTS = [
    'beta.ara-api.sparcs.org',
    'ara-api.sparcs.org',
]

SSO_IS_BETA = False

MIDDLEWARE += [
    'django.middleware.csrf.CsrfViewMiddleware',
]
