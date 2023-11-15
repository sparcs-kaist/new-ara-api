from django.db import models
from django.utils.translation import gettext_lazy

from ara.db.models import MetaDataModel


class Calendar(MetaDataModel):
    tag = models.IntegerField()
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
    ko_title = models.CharField(
        verbose_name="한글 제목",
        max_length=512,
    )
    en_title = models.CharField(
        verbose_name="영어 제목",
        max_length=512,
    )
