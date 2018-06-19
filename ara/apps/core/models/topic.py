from django.db import models

from ara.db.models import MetaDataModel


class Topic(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '말머리'
        verbose_name_plural = '말머리 목록'
        unique_together = (
            ('ko_name', 'deleted_at'),
            ('en_name', 'deleted_at'),
        )

    ko_name = models.CharField(
        max_length=32,
        verbose_name='말머리 국문 이름',
    )
    en_name = models.CharField(
        max_length=32,
        verbose_name='말머리 영문 이름',
    )
    ko_description = models.TextField(
        verbose_name='말머리 국문 소개',
    )
    en_description = models.TextField(
        verbose_name='말머리 영문 소개',
    )

    parent_board = models.ForeignKey(
        to='core.Board',
        db_index=True,
        related_name='topic_set',
        verbose_name='상위 게시판'
    )

    def __str__(self):
        return self.ko_name
