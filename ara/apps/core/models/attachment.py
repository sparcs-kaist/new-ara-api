from django.db import models

from ara.classes.model import MetaDataModel


class Attachment(MetaDataModel):
    class Meta:
        verbose_name = '첨부파일'
        verbose_name_plural = '첨부파일'

    file = models.FileField(
        verbose_name='링크',
    )
