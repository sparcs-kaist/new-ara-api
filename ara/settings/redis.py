from datetime import timedelta
from os import environ as os_environ


REDIS_HOST = os_environ.get("NEWARA_REDIS_ADDRESS", "localhost")
REDIS_DATABASE = int(os_environ.get("NEWARA_REDIS_DATABASE", 0))
REDIS_URL = f"redis://{REDIS_HOST}:6379/{REDIS_DATABASE}"

CACHES_TIMEOUT = timedelta(days=14)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": CACHES_TIMEOUT,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
