from django.db import models

from ara.classes.model import MetaDataModel


class BestComment(MetaDataModel):
    class Meta:
        verbose_name = '베스트 댓글'
        verbose_name_plural = '베스트 댓글'

    comment = models.OneToOneField(
        to='core.Comment',
        db_index=True,
        related_name='best',
        verbose_name='댓글',
    )
