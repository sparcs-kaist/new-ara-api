from apps.core.models import Article, Comment, Notification, NotificationReadLog
from ara.domain.notification.type import NotificationInfo
from ara.infra.django_infra import AraDjangoInfra


class NotificationInfra(AraDjangoInfra[Notification]):
    def __init__(self, user_id: int) -> None:
        super().__init__(Notification)
        self.user_id = user_id

    def get_all_notifications(self, user_id: int) -> list[NotificationInfo]:
        queryset = Notification.objects.select_related(
            "related_article",
            "related_comment",
        ).prefetch_related(
            "related_article__attachments",
            NotificationReadLog.prefetch_my_notification_read_log(user_id),
        )
        return [self._to_notification_info(notification) for notification in queryset]

    def _to_notification_info(self, notification: Notification) -> NotificationInfo:
        return NotificationInfo(
            id=notification.id,  # 이렇게 써도 되나요?
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

    """
    ##수정해야함##

    def create_notification(self, article: Article, comment: Comment) -> None:
        if comment.parent_comment:
            parent_comment = comment.parent_comment
            related_comment = parent_comment
        else:
            related_comment = None

        related_article = comment.parent_article if comment.parent_article else parent_comment.parent_article

        title = f"{article.title}에 새로운 {'대댓글' if parent_comment else '댓글'}이 작성되었습니다."
        content = comment.content[:32]

        Notification.objects.create(
            type="comment_commented" if parent_comment else "article_commented",
            title=title,
            content=content,
            related_article=related_article,
            related_comment=related_comment,
        )
    """
