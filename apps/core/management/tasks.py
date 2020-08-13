from ara import celery_app


@celery_app.task
def crawl_portal():
    print('crawling!')
