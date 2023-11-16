from django.db import models

from ara.db.models import MetaDataModel


class Calendar(MetaDataModel):
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
    ko_description = models.CharField(
        verbose_name="한글 설명",
        max_length=512,
    )
    en_description = models.CharField(
        verbose_name="영어 설명",
        max_length=512,
    )
    location = models.CharField(
        verbose_name="위치",
        max_length=512,
    )
    url = models.URLField(
        verbose_name="포탈 링크",
        max_length=200,
        blank=True,
        null=True,
        default=None,
    )
    tags = models.ManyToManyField("Tag", related_name="calendars")

    def __str__(self):
        return self.ko_title


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    color = models.CharField(max_length=7, default="#000000")
    calendar = models.ForeignKey(
        "Calendar", on_delete=models.SET_NULL, null=True, blank=True
    )
