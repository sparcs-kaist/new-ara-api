from django.db import models
from django.utils import timezone

from ara.db.models import MetaDataModel


class CommunicationArticle(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '소통 게시물'
        verbose_name_plural = '소통 게시물 목록'
    
    article_id = models.OneToOneField(
        to='core.Article',
        on_delete=models.CASCADE,
        db_index=True,
        verbose_name='게시물',
    )

    response_deadline = models.DateTimeField(
        null=True,
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='답변 요청 기한',
    )
    
    confirmed_by_school_at = models.BooleanField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='학교측 문의 확인 시각',
    )

    answered_at = models.BooleanField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='학교측 답변을 받은 시각',
    )
