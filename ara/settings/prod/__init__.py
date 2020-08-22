from ara.settings import MIDDLEWARE, REST_FRAMEWORK

DEBUG = False

ALLOWED_HOSTS = [
    'newara.sparcs.org',
    'ara.sparcs.org',
]

SSO_IS_BETA = False

SESSION_COOKIE_SAMESITE = 'Strict'

MIDDLEWARE += [
    'django.middleware.csrf.CsrfViewMiddleware',
]

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'rest_framework.authentication.SessionAuthentication',
)

