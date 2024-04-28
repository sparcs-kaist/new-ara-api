from pydantic import BaseModel
from typing import Optional

class NotificationInfo(BaseModel): 
    id: int
    type: str
    title: str
    content: str
    related_article_id: int | None
    related_comment_id: Optional[int]
    is_read: bool
