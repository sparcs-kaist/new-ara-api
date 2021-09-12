from os import environ

from ara.settings import *


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

REDIS_DATABASE = int(environ.get('NEWARA_REDIS_DATABASE', 2))
REDIS_URL = f'redis://{REDIS_HOST}:6379/{REDIS_DATABASE}'

CELERY_TASK_ALWAYS_EAGER = True
ELASTICSEARCH_INDEX_NAME = 'articles_test'