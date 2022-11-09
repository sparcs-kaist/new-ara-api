import os

import sentry_sdk
from sentry_sdk.integrations import celery, django, redis

sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        celery.CeleryIntegration(),
        django.DjangoIntegration(),
        redis.RedisIntegration(),
    ],
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)
