import datetime

from django.db import models
from django.conf import settings

from django_mysql.models import JSONField

from ara.db.models import MetaDataModel, MetaDataManager, MetaDataQuerySet


class ArticleReadLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시물 조회 기록'
        verbose_name_plural = '게시물 조회 기록 목록'

    read_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name='article_read_log_set',
        verbose_name='조회자',
    )
    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Article',
        related_name='article_read_log_set',
        verbose_name='조회된 게시글',
    )

    def __str__(self) -> str:
        return str(self.read_by) + "/" + str(self.article)

    @property
    def last_read_at(self) -> datetime:
        return self.updated_at

    @classmethod
    def prefetch_my_article_read_log(cls, user, prefix='') -> models.Prefetch:
        return models.Prefetch(
            '{}article_read_log_set'.format(prefix),
            queryset=ArticleReadLog.objects.filter(
                read_by=user,
            ),
        )


class ArticleUpdateLogQuerySet(MetaDataQuerySet):
    def create(self, article, updated_by):
        from apps.core.serializers.article import BaseArticleSerializer

        return super().create(**{
            'data': BaseArticleSerializer(article).data,
            'article': article,
            'updated_by': updated_by,
        })


class ArticleUpdateLogManager(MetaDataManager):
    pass


class ArticleUpdateLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시물 변경 기록'
        verbose_name_plural = '게시물 변경 기록 목록'

    objects = ArticleUpdateLogManager.from_queryset(queryset_class=ArticleUpdateLogQuerySet)()

    data = JSONField()

    updated_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name='article_update_log_set',
        verbose_name='변경자',
    )
    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Article',
        related_name='article_update_log_set',
        verbose_name='변경된 게시글',
    )

    def __str__(self) -> str:
        return str(self.updated_by) + "/" + str(self.article)


class ArticleDeleteLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시물 삭제 기록'
        verbose_name_plural = '게시물 삭제 기록 목록'

    deleted_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name='article_delete_log_set',
        verbose_name='삭제자',
    )
    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Article',
        related_name='article_delete_log_set',
        verbose_name='삭제된 게시글',
    )

    def __str__(self) -> str:
        return str(self.deleted_by) + "/" + str(self.article)
