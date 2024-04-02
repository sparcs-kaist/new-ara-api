from pydantic import BaseModel
from typing import Optional

class Notification(BaseModel):
    id: int
    type: str
    title: str
    content: str
    related_article_id: Optional[int]
    related_comment_id: Optional[int]
    is_read: bool

    class Config:
        orm_mode = True