from apps.core.models import Notification, NotificationReadLog
from ara.domain.notification.type import NotificationInfo
from ara.infra.notification.notification_infra import NotificationInfra


class NotificationDomain:
    def __init__(self) -> None:
        self.notification_infra = NotificationInfra()

    def get_all_notifications(self, user_id: int) -> list[NotificationInfo]:
        return self.notification_infra.get_all_notifications(user_id)

    def get_unread_notifications(self, user_id: int) -> list[NotificationInfo]:
        notifications = self.notification_infra.get_all_notifications(user_id)
        return [
            notification
            for notification in notifications
            if NotificationReadLog.objects.filter(
                notification=notification, read_by=user_id, is_read=False
            ).exists()
        ]

    def read_all_notifications(self, user_id: int) -> None:
        return self.notification_infra.read_all_notifications(user_id)

    def read_notification(self, user_id: int, notification_id: int) -> None:
        return self.notification_infra.read_notification(user_id, notification_id)

    def create_notification(self, notification_info: NotificationInfo):
        return self.notification_infra.create_notification(notification_info)
