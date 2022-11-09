import os
import uuid

from django.db import models

from ara.db.models import MetaDataModel


class Attachment(MetaDataModel):
    def _hash_filename(instance, filename):
        s3_folder = "files/"
        _, extension = os.path.splitext(filename)
        unique_filename = str(uuid.uuid4()) + extension
        return os.path.join(s3_folder, unique_filename)

    class Meta(MetaDataModel.Meta):
        verbose_name = "첨부파일"
        verbose_name_plural = "첨부파일 목록"

    file = models.FileField(
        upload_to=_hash_filename,
        verbose_name="링크",
        max_length=200,
    )

    size = models.BigIntegerField(
        default=-1,
        verbose_name="용량",
    )

    mimetype = models.CharField(
        default="text/plain",
        max_length=128,
        verbose_name="타입",
    )
