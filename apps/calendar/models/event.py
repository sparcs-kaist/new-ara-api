from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from ara.db.models import MetaDataModel

if TYPE_CHECKING:
    from .tag import Tag


class Event(MetaDataModel):
    is_all_day = models.BooleanField(
        verbose_name="하루 종일",
        default=False,
    )
    start_at = models.DateTimeField(
        verbose_name="시작 시각",
    )
    end_at = models.DateTimeField(
        verbose_name="종료 시각",
    )

    ko_title = models.CharField(
        verbose_name="한글 제목",
        max_length=512,
    )
    en_title = models.CharField(
        verbose_name="영어 제목",
        max_length=512,
    )
    ko_description = models.TextField(
        verbose_name="한글 설명",
        max_length=512,
        blank=True,
        null=True,
    )
    en_description = models.TextField(
        verbose_name="영어 설명",
        max_length=512,
        blank=True,
        null=True,
    )

    location = models.CharField(
        verbose_name="장소",
        max_length=512,
        blank=True,
        null=True,
    )
    url = models.URLField(
        verbose_name="URL",
        max_length=200,
        blank=True,
        null=True,
    )
    tags: list[Tag] = models.ManyToManyField(
        verbose_name="태그",
        to="calendar.Tag",
        blank=True,
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = "일정"
        verbose_name_plural = "일정 목록"

    def __str__(self) -> str:
        return self.ko_title
