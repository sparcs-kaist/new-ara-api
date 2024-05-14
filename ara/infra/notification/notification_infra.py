from apps.core.models import Article, Comment, Notification, NotificationReadLog
from apps.core.models.board import NameType
from ara.domain.notification.type import NotificationInfo
from ara.firebase import fcm_notify_comment
from ara.infra.django_infra import AraDjangoInfra


class NotificationInfra(AraDjangoInfra[Notification]):
    def __init__(self) -> None:
        super().__init__(Notification)

    def get_all_notifications(self, user_id: int) -> list[NotificationInfo]:
        queryset = Notification.objects.select_related(
            "related_article",
            "related_comment",
        ).prefetch_related(
            "related_article__attachments",
            NotificationReadLog.prefetch_my_notification_read_log(user_id),
        )
        return [self._to_notification_info(notification) for notification in queryset]

    def get_unread_notifications(self, user_id: int) -> list[NotificationInfo]:
        notifications = self.notification_infra.get_all_notifications(user_id)
        return [
            notification
            for notification in notifications
            if NotificationReadLog.objects.filter(
                notification=notification, read_by=user_id, is_read=False
            ).exists()
        ]

    def _to_notification_info(self, notification: Notification) -> NotificationInfo:
        return NotificationInfo(
            id=notification.id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            related_article=notification.related_article,
            related_comment=notification.related_comment,
        )

    def read_all_notifications(self, user_id: int) -> None:
        notifications = self.get_all_notifications(user_id)
        notification_ids = [notification.id for notification in notifications]
        NotificationReadLog.objects.filter(
            notification__in=notification_ids, read_by=user_id
        ).update(is_read=True)

    def read_notification(self, user_id: int, notification_id: int) -> None:
        notification = self.get_by_id(notification_id)
        notification_read_log = NotificationReadLog.objects.get(
            notification=notification, read_by=user_id
        )
        notification_read_log.is_read = True
        notification_read_log.save()

    def get_display_name(self, article: Article, profile: int):
        if article.name_type == NameType.REALNAME:
            return "실명"
        elif article.name_type == NameType.REGULAR:
            return "nickname"
        else:
            return "익명"

    def create_notification(self, comment: Comment) -> None:
        def notify_article_commented(_parent_article: Article, _comment: Comment):
            name = self.get_display_name(_parent_article, _comment.created_by_id)
            title = f"{name} 님이 새로운 댓글을 작성했습니다."

            notification = Notification(
                type="article_commented",
                title=title,
                content=_comment.content[:32],
                related_article=_parent_article,
                related_comment=None,
            )
            notification.save()

            NotificationReadLog.objects.create(
                read_by=_parent_article.created_by,
                notification=notification,
            )

            fcm_notify_comment(
                _parent_article.created_by,
                title,
                _comment.content[:32],
                f"post/{_parent_article.id}",
            )

        def notify_comment_commented(_parent_article: Article, _comment: Comment):
            name = self.get_display_name(_parent_article, _comment.created_by_id)
            title = f"{name} 님이 새로운 대댓글을 작성했습니다."

            notification = Notification(
                type="comment_commented",
                title=title,
                content=_comment.content[:32],
                related_article=_parent_article,
                related_comment=_comment.parent_comment,
            )
            notification.save()

            NotificationReadLog.objects.create(
                read_by=_comment.parent_comment.created_by,
                notification=notification,
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
