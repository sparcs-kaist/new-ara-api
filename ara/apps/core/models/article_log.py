import datetime

from django.db import models

from django_mysql.models import JSONField

from ara.classes.model import MetaDataModel, MetaDataManager, MetaDataQuerySet


class ArticleReadLog(MetaDataModel):
    class Meta:
        verbose_name = '게시물 조회 기록'
        verbose_name_plural = '게시물 조회 기록'

    read_by = models.ForeignKey(
        to='auth.User',
        related_name='article_read_log_set',
        verbose_name='조회자',
    )
    article = models.ForeignKey(
        to='core.Article',
        related_name='article_read_log_set',
        verbose_name='조회된 게시글',
    )

    @property
    def last_read_at(self):
        return self.updated_at if self.updated_at != datetime.datetime.min else self.created_at

    def __str__(self):
        return str(self.read_by) + "/" + str(self.article)


class ArticleUpdateLogQuerySet(MetaDataQuerySet):
    def create(self, article, updated_by):
        from apps.core.serializers.article import ArticleSerializer

        return super().create(**{
            'data': ArticleSerializer(article).data,
            'article': article,
            'updated_by': updated_by,
        })


class ArticleUpdateLogManager(MetaDataManager):
    pass


class ArticleUpdateLog(MetaDataModel):
    class Meta:
        verbose_name = '게시물 변경 기록'
        verbose_name_plural = '게시물 변경 기록'

    objects = ArticleUpdateLogManager.from_queryset(queryset_class=ArticleUpdateLogQuerySet)()

    data = JSONField()

    updated_by = models.ForeignKey(
        to='auth.User',
        related_name='article_update_log_set',
        verbose_name='변경자',
    )
    article = models.ForeignKey(
        to='core.Article',
        related_name='article_update_log_set',
        verbose_name='변경된 게시글',
    )

    def __str__(self):
        return str(self.updated_by) + "/" + str(self.article)


class ArticleDeleteLog(MetaDataModel):
    class Meta:
        verbose_name = '게시물 삭제 기록'
        verbose_name_plural = '게시물 삭제 기록'

    deleted_by = models.ForeignKey(
        to='auth.User',
        related_name='article_delete_log_set',
        verbose_name='삭제자',
    )
    article = models.ForeignKey(
        to='core.Article',
        related_name='article_delete_log_set',
        verbose_name='삭제된 게시글',
    )

    def __str__(self):
        return str(self.deleted_by) + "/" + str(self.article)
