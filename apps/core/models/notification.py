from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils.functional import cached_property

from apps.core.models import Article, Comment
from apps.core.models.board import NameType
from ara.db.models import MetaDataModel
from ara.firebase import fcm_notify_comment

from apps.chatting.models.room import ChatRoom
from apps.chatting.models.message import ChatMessage
from apps.chatting.models.membership_room import ChatRoomMemberShip

from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()

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
    related_chat_room = models.ForeignKey(
        verbose_name = "알림 관련 채팅방",
        to = "chatting.ChatRoom",
        on_delete = models.CASCADE,
        related_name = "notification_set",
        null = True,
        db_index = True,
        default = None,
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

    @classmethod
    @transaction.atomic
    def notify_message(cls, message : ChatMessage):
        from apps.core.models import NotificationReadLog

        # 채팅방 알림을 만드는 logic flow :
        # 1. message가 보내진 채팅방 찾기
        _messaged_room : ChatRoom = message.chat_room

        # 2. 채팅방에 있는 User들 의 Membership 찾기
        _memberships : list[ChatRoomMemberShip] = ChatRoomMemberShip.objects.filter(chat_room=_messaged_room)

        # 3. Membership 에서, 메시지 작성자와, read_at 이 message_create 시점 이전인지 찾기
        _unread_memberships = [
            membership for membership in _memberships
            if membership.user != message.created_by and (
                membership.last_seen_at is None or membership.last_seen_at < message.created_at
            )
        ]

        #같은 notification을 여러번 보내야 하므로 notification 먼저 생성
        notification = cls.objects.create(
            type="chat_message",
            title=f"새로운 메시지가 도착했습니다.",
            content=f"{_messaged_room.room_title}에 읽지 않은 메시지가 있습니다.",
            related_chat_room=_messaged_room,
        )

        def notify_chat_room_message(_notify_to : User):
            NotificationReadLog.objects.create(
                read_by=_notify_to,
                notification=notification
            )
            # @Todo : FCM 붙이기

        # 과정이 느리니까 message create 에서 async로 돌리기.
        for membership in _unread_memberships:
            # 4. 이미 읽지 않은 알림이 있는지 확인
            if NotificationReadLog.objects.filter(
                read_by=membership.user,
                notification__related_chat_room=_messaged_room,
                notification__created_at__gte=message.created_at,
                is_read=False
            ).exists():
                continue

            # 5. 대상 User에게 알림 보내기
            notify_chat_room_message(membership.user)
