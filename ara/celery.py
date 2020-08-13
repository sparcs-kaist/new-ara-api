import os
from datetime import timedelta

from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ara.settings")

app = Celery('ara')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.result_expires = timedelta(days=1)  # default도 하루임

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(['apps.core.management.tasks'])
app.conf.timezone = 'Asia/Seoul'

# Task 등록시 이름은 동사로 시작하도록 합시다
app.conf.beat_schedule = {
    'crawl_portal': {
        'task': 'apps.core.management.tasks.crawl_portal',
        'schedule': settings.SCHEDULERS['CRAWL_PORTAL']['CRONTAB'],
        'args': []
    },
    'save_daily_best': {
        'task': 'apps.core.management.tasks.save_daily_best',
        'schedule': settings.SCHEDULERS['SAVE_DAILY_BEST']['CRONTAB'],
        'args': []
    },
    'save_monthly_best': {
        'task': 'apps.core.management.tasks.save_monthly_best',
        'schedule': settings.SCHEDULERS['SAVE_MONTHLY_BEST']['CRONTAB'],
        'args': []
    },
}
