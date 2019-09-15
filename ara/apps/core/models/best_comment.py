from django.db import models

from ara.db.models import MetaDataModel


PERIOD_CHOICES = (
    ('daily', 'daily'),
    ('weekly', 'weekly'),
)

BEST_BY_CHOICES = (
    ('positive_vote_count', 'positive_vote_count'),
    ('hit_count', 'hit_count')
)


class BestComment(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '베스트 댓글'
        verbose_name_plural = '베스트 댓글 목록'

    period = models.CharField(
        choices=PERIOD_CHOICES,
        default='daily',
        max_length=32,
        verbose_name='베스트 댓글 종류',
    )
    best_by = models.CharField(
        choices=BEST_BY_CHOICES,
        default='positive_vote_count',
        max_length=32,
        verbose_name="베스트 댓글 선정 기준"
    )

    comment = models.OneToOneField(
        on_delete=models.CASCADE,
        to='core.Comment',
        db_index=True,
        related_name='best',
        verbose_name='댓글',
    )
