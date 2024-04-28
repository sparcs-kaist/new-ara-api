from ara.domain.notification.type import NotificationInfo
from ara.infra.notification.notification_infra import NotificationInfra

class NotificationDomain:
    def __init__(self) -> None:
        self.notification_infra = NotificationInfra()
        
    def get_all_notifications(self) -> list[NotificationInfo]:
        return self.notification_infra.get_all_notifications()
    
    class Config:
        orm_mode = True