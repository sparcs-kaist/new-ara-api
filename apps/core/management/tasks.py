import time
from collections import defaultdict

from apps.core.management.scripts.reminder_email_for_reply import send_email
from apps.core.models import BestArticle
from apps.kaist.portal.worker import Worker as PortalCrawlWorker
from apps.core.management.scripts.meal_crawler import crawl_daily_meal

from ara import celery_app, redis
from datetime import datetime, timedelta



@celery_app.task
def crawl_portal():
    PortalCrawlWorker.fetch_and_save_from_the_latest(batch_size=32)


def _get_redis_key(type_):
    return f"articles:{type_}"


def _get_best(days, period):
    BestArticle.objects.filter(latest=True, period=period).update(latest=False)

    type_ = "vote"
    to_ts = time.time()
    from_ts = to_ts - 24 * 60 * 60 * days

    vote_objs = redis.get_objs_by_values(_get_redis_key(type_), f"({from_ts}", to_ts)

    article_votes = defaultdict(int)
    for obj in vote_objs:
        article_id, vote, _, _ = obj.split(":")
        article_votes[article_id] += int(vote)

    type_ = "hit"
    hit_objs = redis.get_objs_by_values(_get_redis_key(type_), f"({from_ts}", to_ts)

    article_hits = defaultdict(int)
    for obj in hit_objs:
        article_id, hit, _, _ = obj.split(":")
        article_hits[article_id] += int(hit)

    hit_sorted = sorted(
        article_votes.items(), key=lambda x: article_hits[x[0]], reverse=True
    )
    articles = []
    keys = []

    length = len(article_votes)
    for key, _ in sorted(hit_sorted, key=lambda x: x[1], reverse=True)[:5]:
        articles.append(BestArticle(period=period, article_id=key, latest=True))
        keys.append(key)

    if length < 5:
        for key, _ in sorted(article_hits.items(), key=lambda x: x[1], reverse=True):
            if key not in keys:
                articles.append(BestArticle(period=period, article_id=key, latest=True))
                keys.append(key)

            if len(articles) >= 5:
                break

    return BestArticle.objects.bulk_create(articles)


@celery_app.task
def save_daily_best():
    return _get_best(1, BestArticle.PERIOD_CHOICES_DAILY)


@celery_app.task
def save_weekly_best():
    return _get_best(7, BestArticle.PERIOD_CHOICES_WEEKLY)


@celery_app.task
def send_email_for_reply_reminder():
    send_email()

@celery_app.task
def crawl_meal():
    #현재 날짜로 부터 앞으로 일주일간 식단 크롤링
    # 현재 날짜를 가져오기
    current_date = datetime.now()

    # 앞 뒤 7일간의 날짜 리스트 생성
    # 이전 날짜 7일에 경우 학식이 변경된 경우를 아직 처리하지 못 해서 보류. 미래 7일만 가져온다.
    dates = [(current_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(0, 7)]
    for date in dates:
        #식단 크롤링
        crawl_daily_meal(date)
        time.sleep(2)
