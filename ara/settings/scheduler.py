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
    ),  # 매분
    "CRAWL_MEAL": create_scheduler_config(
        "CRAWL_MEAL", crontab=crontab(hour=5, minute=0)
    ),  # 매일 오전 5시
    "CRAWL_MEAL_PHOTOS": create_scheduler_config(
        "CRAWL_MEAL_PHOTOS", crontab=crontab(minute="*/10")
    ),  # 10분마다, 끼니 구간 밖이면 바로 끝난다
}


def env_map(name, default):
    raw = os_environ.get(name, default)
    return dict(item.strip().split("=", 1) for item in raw.split(",") if item.strip())


# 인스타 계정=식당 code
MEAL_PHOTO_INSTAGRAM_ACCOUNTS = env_map("NEWARA_MEAL_PHOTO_INSTAGRAM_ACCOUNTS", "gaon_kaist_n11=fclt")
# 끼니=HH:MM-HH:MM (KST). 이 구간에 올라온 게시물만, 이 구간에만 수집한다
MEAL_PHOTO_WINDOWS = {
    meal_time: tuple(span.split("-"))
    for meal_time, span in env_map(
        "NEWARA_MEAL_PHOTO_WINDOWS", "BREAKFAST=07:00-09:30,LUNCH=10:30-13:30,DINNER=16:30-19:00",
    ).items()
}

# 크롤링 뒤에서 기다리지 않도록 (worker 는 supervisor-celery-worker.conf). 푸시 큐는 apps/core/push.py 에서 고른다
CELERY_TASK_ROUTES = {
    "apps.core.management.tasks.send_push_to_user": {"queue": "push"},
    "apps.core.management.tasks.send_push_to_users": {"queue": "push"},
    "apps.core.management.tasks.sweep_delivery_deadlines": {"queue": "urgent"},
}
