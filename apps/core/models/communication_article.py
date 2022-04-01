from django.db import models
from django.utils import timezone
from django.contrib import admin

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

    school_response_status = models.SmallIntegerField(
        default=0,
        verbose_name='답변 진행 상황',
    )
    
    @admin.display(description='진행 상황')
    def get_status_string(self) -> str:
        status_list = ['소통 중', '답변 대기 중', '답변 준비 중', '답변 완료']
        return status_list[self.school_response_status]
    
    def __str__(self):
        return self.article.title