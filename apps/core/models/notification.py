from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.functional import cached_property

from apps.core.models import Article, Comment
from apps.core.models.board import NameType
from ara.db.models import MetaDataModel
from ara.firebase import fcm_notify_comment

if TYPE_CHECKING:
    from apps.user.models import UserProfile

TYPE_CHOICES = (
    ("default", "default"),
    ("article_commented", "article_commented"),
    ("comment_commented", "comment_commented"),
)


class Notification(MetaDataModel):
    type = models.CharField(
        verbose_name="알림 종류",
        choices=TYPE_CHOICES,
        default="default",
        max_length=32,
    )
    title = models.CharField(
        verbose_name="제목",
        max_length=256,
    )
    content = models.TextField(
        verbose_name="내용",
    )

    related_article = models.ForeignKey(
        verbose_name="알림 관련 제보",
        to="core.Article",
        on_delete=models.CASCADE,
        related_name="notification_set",
        null=True,
        db_index=True,
    )
    related_comment = models.ForeignKey(
        verbose_name="알림 관련 댓글",
        to="core.Comment",
        on_delete=models.CASCADE,
        related_name="notification_set",
        null=True,
        db_index=True,
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = "알림"
        verbose_name_plural = "알림 목록"

    @cached_property
    def data(self) -> dict:
        return {
            "title": self.title,
            "body": self.content,
            "icon": "",
            "click_action": "",
        }

    @staticmethod
    def get_display_name(article: Article, profile: UserProfile):
        if article.name_type == NameType.REALNAME:
            return profile.realname
        elif article.name_type == NameType.REGULAR:
            return profile.nickname
        else:
            return "익명"

    @classmethod
    def notify_commented(cls, comment):
        from apps.core.models import NotificationReadLog

        def notify_article_commented(_parent_article: Article, _comment: Comment):
            name = cls.get_display_name(_parent_article, _comment.created_by.profile)
            title = f"{name} 님이 새로운 댓글을 작성했습니다."

            NotificationReadLog.objects.create(
                read_by=_parent_article.created_by,
                notification=cls.objects.create(
                    type="article_commented",
                    title=title,
                    content=_comment.content[:32],
                    related_article=_parent_article,
                    related_comment=None,
                ),
            )
            fcm_notify_comment(
                _parent_article.created_by,
                title,
                _comment.content[:32],
                f"post/{_parent_article.id}",
            )

        def notify_comment_commented(_parent_article: Article, _comment: Comment):
            name = cls.get_display_name(_parent_article, _comment.created_by.profile)
            title = f"{name} 님이 새로운 대댓글을 작성했습니다."

            NotificationReadLog.objects.create(
                read_by=_comment.parent_comment.created_by,
                notification=cls.objects.create(
                    type="comment_commented",
                    title=title,
                    content=_comment.content[:32],
                    related_article=_parent_article,
                    related_comment=_comment.parent_comment,
                ),
            )
            fcm_notify_comment(
                _comment.parent_comment.created_by,
                title,
                _comment.content[:32],
                f"post/{_parent_article.id}",
            )

        article = (
            comment.parent_article
            if comment.parent_article
            else comment.parent_comment.parent_article
        )

        if comment.created_by != article.created_by:
            notify_article_commented(article, comment)

        if (
            comment.parent_comment
            and comment.created_by != comment.parent_comment.created_by
        ):
            notify_comment_commented(article, comment)
