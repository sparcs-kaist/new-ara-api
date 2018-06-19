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


class BestArticle(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '베스트 문서'
        verbose_name_plural = '베스트 문서 목록'

    period = models.CharField(
        choices=PERIOD_CHOICES,
        default='daily',
        max_length=32,
        verbose_name='베스트 문서 종류',
    )
    best_by = models.CharField(
        choices=BEST_BY_CHOICES,
        default='positive_vote_count',
        max_length=32,
        verbose_name="베스트 문서 선정 기준"
    )

    article = models.OneToOneField(
        to='core.Article',
        db_index=True,
        related_name='best',
        verbose_name='문서',
    )
