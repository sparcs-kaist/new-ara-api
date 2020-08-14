from django.db import models

from ara.db.models import MetaDataModel


class BestArticle(MetaDataModel):
    PERIOD_CHOICES_DAILY = 'daily'
    PERIOD_CHOICES_WEEKLY = 'weekly'
    PERIOD_CHOICES = (
        (PERIOD_CHOICES_DAILY, PERIOD_CHOICES_DAILY),
        (PERIOD_CHOICES_WEEKLY, PERIOD_CHOICES_WEEKLY),
    )

    BEST_BY_CHOICES_POSITIVE_VOTES = 'positive_vote_count'
    BEST_BY_CHOICES = (
        (BEST_BY_CHOICES_POSITIVE_VOTES, BEST_BY_CHOICES_POSITIVE_VOTES),
    )

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

    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Article',
        db_index=True,
        related_name='best_set',
        verbose_name='문서',
    )
