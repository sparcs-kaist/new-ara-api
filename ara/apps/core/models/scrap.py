from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class Scrap(MetaDataModel):
    class Meta:
        verbose_name = '스크랩'
        verbose_name_plural = '스크랩'

    scrapped_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='scrap_set',
        verbose_name='스크랩한 사람',
    )
    article = models.ForeignKey(
        to='core.Article',
        related_name='scrap_set',
        verbose_name='글',
    )

