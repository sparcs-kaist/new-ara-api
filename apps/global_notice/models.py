from django.db import models

from ara.db.models import MetaDataModel


class GlobalNotice(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "글로벌 공지"
        verbose_name_plural = "글로벌 공지 목록"

    ko_title = models.CharField(verbose_name="한글 제목", max_length=256)
    en_title = models.CharField(verbose_name="영문 제목", max_length=256)
    ko_content = models.TextField(verbose_name="한글 본문")
    en_content = models.TextField(verbose_name="영문 본문")
    started_at = models.DateTimeField(verbose_name="모달 노출 시작 시간")
    expired_at = models.DateTimeField(verbose_name="모달 노출 종료 시간")
