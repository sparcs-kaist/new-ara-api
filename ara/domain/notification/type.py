from typing import Optional

from pydantic import BaseModel

from apps.core.models import Article, Comment, Notification


class NotificationReadLogInfo(BaseModel):
    is_read: bool
    read_by: int
    notification: Notification

    class Config:
        arbitrary_types_allowed = True


class NotificationInfo(BaseModel):
    id: int
    type: str
    title: str
    content: str
    related_article: Article | None
    related_comment: Optional[Comment]

    class Config:
        arbitrary_types_allowed = True
