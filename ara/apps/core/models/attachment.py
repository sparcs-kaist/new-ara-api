from django.db import models

from ara.db.models import MetaDataModel


class Attachment(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '첨부파일'
        verbose_name_plural = '첨부파일 목록'

    file = models.FileField(
        verbose_name='링크',
    )
