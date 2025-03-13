from datetime import timedelta
from os import environ as os_environ

from celery.schedules import crontab

from .django import TIME_ZONE
from .redis import REDIS_URL

# Celery
CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_WORKER_CONCURRENCY = os_environ.get("NEWARA_CELERY_CONCURRENCY")
CELERY_ACCEPT_CONTENT = ["json", "pickle"]  # datetime때문에 pickle 사용
CELERY_EVENT_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_TASK_SERIALIZER = "pickle"
CELERY_TASK_RESULT_EXPIRES = int(os_environ.get("NEWARA_CELERY_EXPIRES", 600))


def create_scheduler_config(name, period=None, crontab=None):
    config = {"NAME": name, "PING_URL": os_environ.get(f"NEWARA_{name}_PING_URL", None)}
    if period is not None:
        config["PERIOD"] = timedelta(
            seconds=int(os_environ.get(f"NEWARA_{name}_PERIOD", period))
        )
    if crontab is not None:
        config["CRONTAB"] = crontab
    return config


SCHEDULERS = {
    "CRAWL_PORTAL": create_scheduler_config(
        name="CRAWL_PORTAL",
        crontab=crontab(minute="*/10"),  # At every 10th minute
    ),
    "SAVE_DAILY_BEST": create_scheduler_config(
        name="SAVE_DAILY_BEST",
        crontab=crontab(minute="0"),
    ),
    "SAVE_WEEKLY_BEST": create_scheduler_config(
        name="SAVE_WEEKLY_BEST",
        crontab=crontab(minute="0"),
    ),
    "SEND_EMAIL_FOR_REPLY_REMINDER": create_scheduler_config(
        name="SEND_EMAIL_FOR_REPLY_REMINDER",
        crontab=crontab(minute="0", hour="7"),  # At 07:00 AM
    ),
}
