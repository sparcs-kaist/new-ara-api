from typing import List
import logging
from ara.domain.notification.type import NotificationInfo
from ara.infra.django_infra import AraDjangoInfra
from apps.core.models import Notification, NotificationReadLog


class NotificationInfra(AraDjangoInfra[Notification]):
    def __init__(self) -> None:
        super().__init__(Notification)
        
    def get_all_notifications(self) -> list[NotificationInfo]:

        queryset = Notification.objects.filter(
                notification_read_log_set__read_by=self.request.user,
            ).select_related(
                "related_article",
                "related_comment",
            ).prefetch_related(
                "related_article__attachments",
                NotificationReadLog.prefetch_my_notification_read_log(
                    self.request.user
                ),
            )
        
        notifications_info = [self._to_notification_info(notification) for notification in queryset]
        return notifications_info


    def _to_notification_info(self, notification: Notification) -> NotificationInfo:
      return NotificationInfo(
        id=notification.id,
        type=notification.type,
        title=notification.title,
        content=notification.content,
        related_article_id=notification.related_article_id,
        related_comment_id=notification.related_comment_id,
        is_read=False
    )
      
    def read_all_notifications(self) -> None:
        notifications = self.get_all_notifications()
        NotificationReadLog.objects.filter(notification__in=notifications, read_by=self.request.user).update(is_read=True)

    def read_notification(self) -> None:
        try:
            notification_read_log = self.get_object().notification_read_log_set.get(
                read_by=self.request.user,
            )

            notification_read_log.is_read = True

            notification_read_log.save()
        except (Notification.DoesNotExist, NotificationReadLog.DoesNotExist) as e:
            logging.error(f"Failed to read notification: {e}")
            