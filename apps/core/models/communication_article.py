import sys

from cached_property import cached_property
from django.db import models
from django.utils import timezone
from django.contrib import admin

from ara.db.models import MetaDataModel

from enum import IntEnum

from ara.settings import MIN_TIME


class SchoolResponseStatus(IntEnum):
    BEFORE_UPVOTE_THRESHOLD = 0
    BEFORE_SCHOOL_CONFIRM = 1
    ANSWER_DONE = 2


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
        primary_key=True,
    )

    response_deadline = models.DateTimeField(
        default=MIN_TIME,
        verbose_name='답변 요청 기한',
    )

    answered_at = models.DateTimeField(
        default=MIN_TIME,
        verbose_name='학교측 답변을 받은 시각',
    )

    school_response_status = models.SmallIntegerField(
        default=SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD,
        verbose_name='답변 진행 상황',
    )
    
    @admin.display(description='진행 상황')
    def get_status_string(self) -> str:
        status_list = ['소통 중', '답변 대기 중', '답변 완료']
        return status_list[self.school_response_status]

    @cached_property
    def days_left(self) -> int:
        if self.response_deadline == MIN_TIME:
            return sys.maxsize
        else:
            return (self.response_deadline.astimezone(timezone.localtime().tzinfo) - timezone.localtime()).days

    def __str__(self):
        return self.article.title
