import os
from os import environ as os_environ

from django.utils.translation import gettext_lazy

from .env import env, root

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = root()


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_extensions",
    "django_s3_storage",
    "django_celery_beat",
    "django_celery_results",
    "drf_spectacular",
    "cacheops",
    "django_elasticsearch_dsl",
    "django_filters",
    "apps.core",
    "apps.user",
    "apps.global_notice",
]

MIDDLEWARE = [
    "ara.log.middleware.LoggingMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ara.classes.middleware.CheckTermsOfServiceMiddleware",
]

ROOT_URLCONF = "ara.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "ara.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "ko-kr"
LANGUAGES = [("ko", gettext_lazy("Korean")), ("en", gettext_lazy("English"))]
LOCALE_PATHS = [os.path.join(BASE_DIR, "ara/locale")]

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": 'SET sql_mode="STRICT_TRANS_TABLES"',
        },
        "NAME": os_environ.get("NEWARA_DB_NAME", "new_ara"),
        "USER": os_environ.get("NEWARA_DB_USER", "root"),
        "PASSWORD": os_environ.get("NEWARA_DB_PASSWORD", ""),
        "HOST": os_environ.get("NEWARA_DB_HOST", "localhost"),
        "PORT": os_environ.get("NEWARA_DB_PORT", "3306"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

STATIC_URL = "/static/"

INTERNAL_IPS = ("127.0.0.1",)

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

EMAIL_BACKEND = "django_ses.SESBackend"

CORS_ALLOW_CREDENTIALS = True
