import configparser

from ara.settings.settings import *


config = configparser.ConfigParser()

config.read(os.path.join(BASE_DIR, 'settings/test/config.cnf'))


DEBUG = True

SECRET_KEY = config.get('SECRET_KEY', 'secret_key')

ALLOWED_HOSTS = [
    '*',
]


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config.get('DB', 'database'),
        'USER': config.get('DB', 'user'),
        'PASSWORD': config.get('DB', 'password'),
        'HOST': config.get('DB', 'host'),
        'PORT': config.get('DB', 'port'),
        'OPTIONS': {
            'charset': 'utf8mb4'
        },
    },
}
