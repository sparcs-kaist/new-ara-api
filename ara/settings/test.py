from os import environ

from .django import *
from .djangorestframework import *
from .s3 import *
from .sso import *


DEBUG = True
TEST = True

DATABASES = {
    'default': { **env.db(),
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        }
    }
}

try:
    from .local_settings import *
except ImportError:
    pass
