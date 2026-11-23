from os import environ

from ara.settings import *

DEBUG = True
TEST = True

# Tests also run in images without the optional development tools.
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]
MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if middleware != "debug_toolbar.middleware.DebugToolbarMiddleware"
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
        "NAME": os_environ.get("NEWARA_DB_NAME", "new_ara"),
        "USER": os_environ.get("NEWARA_DB_USER", "root"),
        "PASSWORD": os_environ.get("NEWARA_DB_PASSWORD", ""),
        "HOST": os_environ.get("NEWARA_DB_HOST", "localhost"),
        "PORT": os_environ.get("NEWARA_DB_PORT", "3306"),
        "TEST": {
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_general_ci",
        },
    }
}

REDIS_DATABASE = int(environ.get("NEWARA_REDIS_DATABASE", 2))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DATABASE}"

CELERY_TASK_ALWAYS_EAGER = True
ELASTICSEARCH_INDEX_NAME = "articles_test"

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda _: False,
}
