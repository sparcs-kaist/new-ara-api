from django.db import models

from ara.db.models import MetaDataModel


class FAQ(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ 목록'

    ko_question = models.CharField(
        max_length=32,
        verbose_name='FAQ 국문 질문',
    )
    en_question = models.CharField(
        max_length=32,
        verbose_name='FAQ 영문 질문',
    )
    ko_answer = models.TextField(
        verbose_name='FAQ 국문 답변',
    )
    en_answer = models.TextField(
        verbose_name='FAQ 영문 답변',
    )

    def __str__(self):
        return self.ko_question
