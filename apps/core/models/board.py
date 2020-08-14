from django.db import models

from django_extensions.db.fields import AutoSlugField

from ara.db.models import MetaDataModel


class Board(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시판'
        verbose_name_plural = '게시판 목록'
        unique_together = (
            ('ko_name', 'deleted_at'),
            ('en_name', 'deleted_at'),
        )

    slug = AutoSlugField(
        populate_from=[
            'en_name',
        ],
    )
    ko_name = models.CharField(
        max_length=32,
        verbose_name='게시판 국문 이름',
    )
    en_name = models.CharField(
        max_length=32,
        verbose_name='게시판 영문 이름',
    )
    ko_description = models.TextField(
        verbose_name='게시판 국문 소개',
    )
    en_description = models.TextField(
        verbose_name='게시판 영문 소개',
    )
    is_kaist = models.BooleanField(
        verbose_name='카이스트 구성원 전용 게시판',
        null=False,
        default=False
    )

    def __str__(self):
        return self.ko_name
