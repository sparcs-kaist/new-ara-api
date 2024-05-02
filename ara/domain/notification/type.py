from typing import Optional

from django.contrib.auth import get_user_model
from pydantic import BaseModel

from apps.core.models import Article, Comment, Notification

User = get_user_model()


class NotificationReadLogInfo(BaseModel):  # 사용 안하는데 ?? 그래도 적어두는게 낫겠죠 ??
    is_read: bool
    read_by: int  # ??? 모르겠다 int ?? user ?? Foreign Key 인데 ??
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
