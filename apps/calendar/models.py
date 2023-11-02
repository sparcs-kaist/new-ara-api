from django.db import models

from ara.db.models import MetaDataModel


class Calendar(MetaDataModel):
    tag = models.ForeignKey(
        verbose_name="태그",
        to="core.Tag",
        on_delete=models.CASCADE,
        related_name="event_set",
        db_index=True,
    )
    is_allday = models.BooleanField(
        verbose_name="하루종일",
        default=False,
    )
    start_at = models.DateTimeField(
        verbose_name="시작 시간",
        blank=True,
        null=True,
        default=None,
    )
    end_at = models.DateTimeField(
        verbose_name="종료 시간",
        blank=True,
        null=True,
        default=None,
    )
    title = models.CharField(
        verbose_name="제목",
        max_length=512,
    )
