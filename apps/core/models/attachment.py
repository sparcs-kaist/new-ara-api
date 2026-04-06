from django.core.validators import FileExtensionValidator
from django.db import models
from ara.db.models import MetaDataModel

class Attachment(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "첨부파일"
        verbose_name_plural = "첨부파일 목록"

    file = models.FileField(
        upload_to="files",
        verbose_name="링크",
        max_length=200,
        validators=[FileExtensionValidator(allowed_extensions=[
            'jpg', 'jpeg', 'png', 'gif', 'webp', 
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
            'zip', 'tar', 'gz', 'mp4', 'mp3'
        ])]
    )

    alias = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="별칭",
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

    def __str__(self) -> str:
        return self.alias or self.file.name
