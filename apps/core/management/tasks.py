import time
from collections import defaultdict

from apps.core.management.scripts.portal_crawler import crawl_hour
from apps.core.models import BestArticle
from ara import celery_app, redis


@celery_app.task
def crawl_portal():
    crawl_hour()


def _get_redis_key(type_):
    return f'articles:{type_}'


def _get_best(days, period):
    type_ = 'vote'
    to_ts = time.time()
    from_ts = to_ts - 24*60*60*days

    vote_objs = redis.get_objs(_get_redis_key(type_), f'({from_ts}', to_ts)

    article_votes = defaultdict(int)
    for obj in vote_objs:
        article_id, vote, _, _ = obj.split(':')
        article_votes[article_id] += int(vote)

    type_ = 'hit'
    hit_objs = redis.get_objs(_get_redis_key(type_), f'({from_ts}', to_ts)

    article_hits = defaultdict(int)
    for obj in hit_objs:
        article_id, hit, _, _ = obj.split(':')
        article_hits[article_id] += int(hit)

    hit_sorted = sorted(article_votes.items(), key=lambda x: article_hits[x[0]], reverse=True)
    articles = []
    keys = []

    length = len(article_votes)
    for key, _ in sorted(hit_sorted, key=lambda x: x[1], reverse=True)[:5]:
        articles.append(BestArticle(period=period,
                                    best_by=BestArticle.BEST_BY_CHOICES_POSITIVE_VOTES,
                                    article_id=key))
        keys.append(key)

    if length < 5:
        for key, _ in sorted(article_hits.items(), key=lambda x: x[1], reverse=True):
            if key not in keys:
                articles.append(BestArticle(period=period,
                                            best_by=BestArticle.BEST_BY_CHOICES_POSITIVE_VOTES,
                                            article_id=key))
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
