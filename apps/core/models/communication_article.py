from django.db import models
from django.utils import timezone

from ara.db.models import MetaDataModel


class CommunicationArticle(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '소통 게시물'
        verbose_name_plural = '소통 게시물 목록'
    
    article = models.OneToOneField(
        to='core.Article',
        on_delete=models.CASCADE,
        related_name='communication_article',
        db_index=True,
        verbose_name='게시물',
    )

    response_deadline = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='답변 요청 기한',
    )
    
    confirmed_by_school_at = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='학교측 문의 확인 시각',
    )

    answered_at = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='학교측 답변을 받은 시각',
    )

    def get_status(self) -> int:
        if self.response_deadline == timezone.datetime.min.replace(tzinfo=timezone.utc):
            return 0
        if self.confirmed_by_school_at == timezone.datetime.min.replace(tzinfo=timezone.utc):
            return 1
        if self.answered_at == timezone.datetime.min.replace(tzinfo=timezone.utc):
            return 2
        return 3
