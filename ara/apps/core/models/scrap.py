from django.db import models

from ara.db.models import MetaDataModel


class Scrap(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '스크랩'
        verbose_name_plural = '스크랩 목록'
        unique_together = (
            ('parent_article', 'scrapped_by', 'deleted_at'),
        )

    parent_article = models.ForeignKey(
        to='core.Article',
        related_name='scrap_set',
        verbose_name='글',
    )
    scrapped_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='scrap_set',
        verbose_name='스크랩한 사람',
    )
