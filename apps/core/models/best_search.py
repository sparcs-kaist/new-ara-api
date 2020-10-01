from django.db import models

from ara.db.models import MetaDataModel


class BestSearch(MetaDataModel):
    REGISTERED_BY_CHOICES_AUTO = 'auto'
    REGISTERED_BY_CHOICES_MANUAL = 'manual'
    REGISTERED_BY_CHOICES = (
        (REGISTERED_BY_CHOICES_AUTO, REGISTERED_BY_CHOICES_AUTO),
        (REGISTERED_BY_CHOICES_MANUAL, REGISTERED_BY_CHOICES_MANUAL),
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = '추천 검색어'
        verbose_name_plural = '추천 검색어 목록'

    ko_word = models.CharField(
        max_length=32,
        verbose_name='검색어 국문',
    )

    en_word = models.CharField(
        max_length=32,
        verbose_name='검색어 영문',
    )

    registered_by = models.CharField(
        choices=REGISTERED_BY_CHOICES,
        default=REGISTERED_BY_CHOICES_MANUAL,
        max_length=32,
        verbose_name="추천 검색어 등록 방법"
    )

    latest = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='최신 추천 검색어',
    )

