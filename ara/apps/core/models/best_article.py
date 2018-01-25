from django.db import models

from ara.classes.model import MetaDataModel


class BestArticle(MetaDataModel):
    class Meta:
        verbose_name = '베스트 문서'
        verbose_name_plural = '베스트 문서'

    article = models.OneToOneField(
        to='core.Article',
        db_index=True,
        related_name='best',
        verbose_name='문서',
    )
