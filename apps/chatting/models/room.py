from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoom(MetaDataModel):
    room_id : int = models.PositiveIntegerField(
        verbose_name = "room_id",
        default = 0,
        index = True,
        unique = True,
    )

    #채팅방의 권한 부여 방식 - 다른 DB 테이블로 빠짐
    room_permission = models.CharField()

    #최근 메시지가 온 시간
    recent_message_at = models.DateTimeField(
        verbose_name= "recent_message_at",
        null = True,
        blank = False,
        auto_now = False,
        default = None,
    )

    #최근 온 메시지의 ID
    recent_message_id = models.PositiveIntegerField(
        verbose_name= "recent_message_id",
        default = None,
        blank = False,
        null = True,
    )

    #created_at : 채팅방 생성 시
    #deleted_at : 채팅방이 삭제되었을 때