from fastapi import APIRouter, Depends, HTTPException
from ara.controller.authentication import get_current_user
from ara.service.notification_service import NotificationService
from ara.domain.user import User
from ara.domain.exceptions import EntityDoesNotExist
from pydantic import BaseModel

router = APIRouter()
notification_service = NotificationService()

class NotificationRead(BaseModel):
    notification_id: int

@router.get("/notifications")
async def list_notifications(current_user: User = Depends(get_current_user)):
    notifications = notification_service.get_notifications_for_user(current_user)
    return notifications

@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: int, current_user: User = Depends(get_current_user)):
    try:
        notification_service.mark_notification_as_read(notification_id, current_user)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Notification not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="You are not allowed to mark this notification as read")
    return {"message": "Notification marked as read successfully"}

@router.post("/notifications/read-all")
async def mark_all_notifications_as_read(current_user: User = Depends(get_current_user)):
    notification_service.mark_all_notifications_as_read(current_user)
    return {"message": "All notifications marked as read successfully"}

@router.post("/notifications/send-push-notification")
async def send_push_notification(notification: NotificationRead, current_user: User = Depends(get_current_user)):
    try:
        notification_service.send_push_notification(notification.notification_id, current_user)
    except EntityDoesNotExist:
        raise HTTPException(status_code=404, detail="Notification not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="You are not allowed to send push notification for this notification")
    return {"message": "Push notification sent successfully"}
