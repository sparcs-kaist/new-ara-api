from os import environ

from .django import *
from .djangorestframework import *
from .s3 import *
from .sso import *
from .scheduler import *


DEBUG = True
TEST = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
        'NAME': os_environ.get('NEWARA_DB_NAME', 'new_ara'),
        'USER': os_environ.get('NEWARA_DB_USER', 'root'),
        'PASSWORD': os_environ.get('NEWARA_DB_PASSWORD', ''),
        'HOST': os_environ.get('NEWARA_DB_HOST', 'localhost'),
        'PORT': os_environ.get('NEWARA_DB_PORT', '3306'),
        'TEST': {
            'CHARSET': 'utf8mb4',
            'COLLATION': 'utf8mb4_general_ci',
        }
    }
}
