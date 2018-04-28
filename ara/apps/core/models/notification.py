from django.db import models

from ara.classes.model import MetaDataModel


TYPE_CHOICES = (
    ('default', 'default'),
    ('article_commented', 'article_commented'),
    ('comment_commented', 'comment_commented'),
)


class Notification(MetaDataModel):
    class Meta:
        verbose_name = '알림'
        verbose_name_plural = '알림'

    type = models.CharField(
        choices=TYPE_CHOICES,
        default='default',
        max_length=32,
        verbose_name='알림 종류',
    )
    title = models.CharField(
        max_length=256,
        verbose_name='제목',
    )
    content = models.TextField(
        verbose_name='내용',
    )

    related_article = models.ForeignKey(
        to='core.Article',
        null=True,
        db_index=True,
        related_name='notification_set',
        verbose_name='알림 관련 제보',
    )
    related_comment = models.ForeignKey(
        to='core.Comment',
        null=True,
        db_index=True,
        related_name='notification_set',
        verbose_name='알림 관련 댓글',
    )

    @property
    def data(self):
        return {
            'title': self.title,
            'body': self.content,
            'icon': '',
            'click_action': '',
        }

    @classmethod
    def notify_commented(cls, comment):
        from apps.core.models import NotificationReadLog

        def notify_article_commented(_article, _comment):
            NotificationReadLog.objects.create(
                read_by=_article.created_by,
                notification=cls.objects.create(
                    type='article_commented',
                    title='회원님의 게시물에 새로운 댓글이 작성되었습니다.',
                    content=_comment.content[:32],
                    related_article=_article,
                    related_comment=_comment,
                ),
            )

        def notify_comment_commented(_article, _comment):
            NotificationReadLog.objects.create(
                read_by=_comment.parent_comment.created_by,
                notification=cls.objects.create(
                    type='comment_commented',
                    title='회원님의 댓글에 새로운 댓글이 작성되었습니다.',
                    content=_comment.content[:32],
                    related_article=_article,
                    related_comment=_comment,
                ),
            )

        if comment.parent_comment:
            if comment.created_by != comment.parent_comment.created_by:
                notify_comment_commented(comment.parent_comment.parent_article, comment)

            if comment.created_by != comment.parent_comment.parent_article.created_by:
                notify_article_commented(comment.parent_comment.parent_article, comment)

        else:
            if comment.created_by != comment.parent_article.created_by:
                notify_article_commented(comment.parent_article, comment)
