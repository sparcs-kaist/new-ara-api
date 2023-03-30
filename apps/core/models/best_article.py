from django.db import models

from ara.db.models import MetaDataModel


class BestArticle(MetaDataModel):
    PERIOD_CHOICES_DAILY = "daily"
    PERIOD_CHOICES_WEEKLY = "weekly"
    PERIOD_CHOICES = (
        (PERIOD_CHOICES_DAILY, PERIOD_CHOICES_DAILY),
        (PERIOD_CHOICES_WEEKLY, PERIOD_CHOICES_WEEKLY),
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = "베스트 게시물"
        verbose_name_plural = "베스트 게시물 목록"

    period = models.CharField(
        choices=PERIOD_CHOICES,
        default="daily",
        db_index=True,
        max_length=32,
        verbose_name="베스트 게시물 종류",
    )

    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Article",
        db_index=True,
        related_name="best_set",
        verbose_name="게시물",
    )

    latest = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="최신 베스트 게시물",
    )
