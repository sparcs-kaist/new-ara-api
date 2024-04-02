from fastapi import HTTPException
from sqlalchemy.orm import Session
from ara.domain.notification import Notification
from ara.domain.user import User
from ara.domain.exceptions import EntityDoesNotExist
from typing import List

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, notification_id: int) -> Notification:
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification

    def save(self, notification: Notification):
        self.db.add(notification)
        self.db.commit()

    def get_notifications_for_user(self, user: User) -> List[Notification]:
        notifications = self.db.query(Notification).filter(Notification.user_id == user.id).all()
        return notifications