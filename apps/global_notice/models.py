from django.db import models

from ara.db.models import MetaDataModel


class GlobalNotice(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "글로벌 공지"
        verbose_name_plural = "글로벌 공지 목록"

    title = models.CharField(verbose_name="제목", max_length=256)
    content = models.TextField(verbose_name="본문")
    started_at = models.DateTimeField(verbose_name="모달 노출 시작 시간")
    expired_at = models.DateTimeField(verbose_name="모달 노출 종료 시간")
