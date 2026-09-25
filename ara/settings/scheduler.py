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
        "CRAWL_PORTAL", crontab=crontab(minute="*/10"),
    ),  # 매 0분 (1시간마다)
    "SAVE_DAILY_BEST": create_scheduler_config(
        "SAVE_DAILY_BEST", crontab=crontab(minute=0)
    ),
    "SAVE_WEEKLY_BEST": create_scheduler_config(
        "SAVE_WEEKLY_BEST", crontab=crontab(minute=0)
    ),
    "SEND_EMAIL_FOR_REPLY_REMINDER": create_scheduler_config(
        "SEND_EMAIL_FOR_REPLY_REMINDER", crontab=crontab(hour=7, minute=0)
    ),  # 매일 오전 7시
    "SWEEP_DELIVERY_DEADLINES": create_scheduler_config(
        "SWEEP_DELIVERY_DEADLINES", crontab=crontab(minute="*")
    ),  # 매분 - 함께 배달 모집 마감 / 방장 결정 시간 초과 처리
    "CRAWL_MEAL": create_scheduler_config(
        "CRAWL_MEAL", crontab=crontab(hour=5, minute=0)
    ),  # 매일 오전 5시
}

# 푸시 / 배달 마감은 크롤링 같은 무거운 작업 뒤에서 기다리지 않도록 urgent 큐로 보낸다
# (urgent 큐만 처리하는 worker 는 .docker/supervisor-celery-worker.conf)
CELERY_TASK_ROUTES = {
    "apps.core.management.tasks.send_push_to_user": {"queue": "urgent"},
    "apps.core.management.tasks.send_push_to_users": {"queue": "urgent"},
    "apps.core.management.tasks.sweep_delivery_deadlines": {"queue": "urgent"},
}
