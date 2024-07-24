from apps.core.models import Comment
from ara.domain.notification.notification_domain import NotificationDomain
from ara.domain.notification.type import NotificationInfo


class NotificationService:
    def __init__(self) -> None:
        self.notification_infra = NotificationDomain()

    def get_all_notifications(self, user_id: int) -> list[NotificationInfo]:
        return self.notification_infra.get_all_notifications(user_id)

    def get_unread_notifications(self, user_id: int) -> list[NotificationInfo]:
        return self.notification_infra.get_unread_notifications(user_id)

    def read_all_notifications(self, user_id: int) -> None:
        return self.notification_infra.read_all_notifications(user_id)

    def read_notification(self, user_id: int, notification_id: int) -> None:
        return self.notification_infra.read_notification(user_id, notification_id)

    def create_notification(self, comment: Comment):
        return self.notification_infra.create_notification(comment)
