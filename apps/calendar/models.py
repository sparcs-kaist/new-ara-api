from django.db import models

from ara.db.models import MetaDataModel


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Calendar(MetaDataModel):
    id = models.AutoField(primary_key=True)
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
    tags = models.ManyToManyField(Tag, related_name="calendars")

    def __str__(self):
        return self.ko_title
