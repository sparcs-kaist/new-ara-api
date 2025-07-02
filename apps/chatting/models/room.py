from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel

class ChatRoomType(str, Enum):
    DM = "DM" # 1:1 채팅방
    GROUP_DM = "GROUP_DM" # 그룹 채팅방 (permission이 없이 유저 모두 동일한 참여자.)
    OPEN_CHAT = "OPEN_CHAT" # 오픈 그룹 채팅방 (role에 따라 permission이 설정된다.)

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoom(MetaDataModel):
    room_id : int = models.PositiveIntegerField(
        verbose_name = "room_id",
        default = 0,
        index = True,
        unique = True,
    )
    # 채팅방 타입
    room_type : ChatRoomType = models.CharFeld(
        verbose_name = "room_type",
        max_length = 20,
        choices = [(room_type.value, room_type.name) for room_type in ChatRoomType],
        default = ChatRoomType.OPEN_CHAT.value,
        blank = False,
        null = False,
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