from django.db import models

from ara.classes.model import MetaDataModel


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

    def __str__(self):
        return str(self.read_by) + "/" + str(self.article)


class ArticleUpdateLog(MetaDataModel):
    class Meta:
        verbose_name = '게시물 변경 기록'
        verbose_name_plural = '게시물 변경 기록'

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

    content = models.TextField(
        verbose_name='본문',
    )

    is_content_sexual = models.BooleanField(
        default=False,
        verbose_name='성인/음란성 내용',
    )

    is_content_social = models.BooleanField(
        default=False,
        verbose_name='정치/사회성 내용',
    )

    use_signature = models.BooleanField(
        default=True,
        verbose_name='서명 사용',
    )

    parent_topic = models.ForeignKey(
        to='core.Topic',
        null=True,
        blank=True,
        default=None,
        db_index=True,
        related_name='article_update_log_set',
        verbose_name='말머리',
    )

    parent_board = models.ForeignKey(
        to='core.Board',
        db_index=True,
        related_name='article_update_log_set',
        verbose_name='게시판',
    )

    def __str__(self):
        return str(self.updated_by) + "/" + str(self.article)

