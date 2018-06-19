from django.db import models

from ara.db.models import MetaDataModel


class Board(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시판'
        verbose_name_plural = '게시판 목록'
        unique_together = (
            ('ko_name', 'deleted_at'),
            ('en_name', 'deleted_at'),
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

    def __str__(self):
        return self.ko_name
