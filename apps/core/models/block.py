import time

from django.db import models, IntegrityError
from django.conf import settings

from ara import redis
from ara.db.models import MetaDataModel


class Block(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '차단'
        verbose_name_plural = '차단 목록'
        unique_together = (
            ('blocked_by', 'user', 'deleted_at'),
        )

    blocked_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name='block_set',
        verbose_name='차단한 사람',
    )

    user = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name='blocked_by_set',
        verbose_name='차단당한 사람',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert self.blocked_by != self.user

        except AssertionError:
            raise IntegrityError('self.user must not be self.blocked_by.')

        super(Block, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

        created = force_insert
        if created:
            pipe = redis.pipeline()
            redis_key = f'blocks:{self.blocked_by_id}'

            pipe.zadd(redis_key, {f'{self.user_id}': time.time()})
            pipe.execute(raise_on_error=True)

    def delete(self, **kwargs):
        super().delete(**kwargs)

        pipe = redis.pipeline()
        redis_key = f'blocks:{self.blocked_by_id}'
        pipe.zrem(redis_key, f'{self.user_id}')

        pipe.execute(raise_on_error=True)

    @classmethod
    def prefetch_my_block(cls, user, prefix=''):
        return models.Prefetch(
            '{}created_by__blocked_by_set'.format(prefix),
            queryset=Block.objects.filter(
                blocked_by=user,
            ),
        )

    @staticmethod
    def is_blocked(blocked_by, user):
        block_objs = redis.get_objs_by_indexes(f'blocks:{blocked_by.id}', 0, -1, (lambda x: int(x)))  # all blocks
        return user.id in block_objs
