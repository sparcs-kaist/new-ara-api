from ara import celery_app


@celery_app.task
def crawl_portal():
    print('crawling!')


@celery_app.task
def save_daily_best():
    print('get daily best!')


@celery_app.task
def save_monthly_best():
    print('get monthly best!')
