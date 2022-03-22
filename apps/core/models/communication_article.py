from django.db import models

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

    need_answer = models.BooleanField(
        default=True,
        verbose_name='답변 요청 여부',
    )
    response_deadline = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='답변 요청 기한',
    )
    
    is_checked_by_school = models.BooleanField(
        default=False,
        verbose_name='학교 답변 여부',
    )
    is_answered = models.Booleanfield(
        default=False,
        verbose_name='답변 완료',
    )
