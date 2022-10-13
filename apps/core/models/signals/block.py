import time

from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Block
from ara import redis
from ara.settings import MIN_TIME


@receiver(models.signals.post_save, sender=Block)
def block_post_save_signal(created, instance, **kwargs):
    def add_block_to_redis(block):
        pipe = redis.pipeline()
        redis_key = f'blocks:{block.blocked_by_id}'
        pipe.zadd(redis_key, {f'{block.user_id}': time.time()})
        pipe.execute(raise_on_error=True)

    def delete_block_from_redis(block):
        pipe = redis.pipeline()
        redis_key = f'blocks:{block.blocked_by_id}'
        pipe.zrem(redis_key, f'{block.user_id}')
        pipe.execute(raise_on_error=True)

    deleted = instance.deleted_at != MIN_TIME

    if created:
        add_block_to_redis(instance)

    elif deleted:
        delete_block_from_redis(instance)
