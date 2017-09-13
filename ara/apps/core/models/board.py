from django.db import models

from ara.classes.model import MetaDataModel


class Board(MetaDataModel):
    class Meta:
        verbose_name = '게시판'
        verbose_name_plural = '게시판'

    ko_name = models.CharField(
        unique=True,
        max_length=32,
        verbose_name='게시판 국문 이름',
    )
    en_name = models.CharField(
        unique=True,
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
