from .env import env
from .django import *
from .djangorestframework import *
from .aws import *
from .sso import *
from .redis import *
from .scheduler import *
from .log import *
from .cacheops import *
from .sentry import *


if env('DJANGO_ENV') == 'development':
    from .dev import *
elif env('DJANGO_ENV') == 'production':
    from .prod import *
