from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel

class ChatMessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    EMOTICON = "EMOTICON"

class ChatMessage(MetaDataModel):
    # 메시지의 종류
    message_type : ChatMessageType = models.CharField(
        max_lenght = 20,
        choices = [(msg_type.value, msg_type.name) for msg_type in ChatMessageType],
        default = ChatMessageType.TEXT.value,
        verbose_name = "message_type",
        blank = False,
        null = False,
    ),
    # 메시지의 고유 ID (room_id, message_id) 순서쌍은 unique
    message_id : int = models.PositiveIntegerField(
        verbose_name = "메시지 ID",
        default = None,
        blank = False,
        null = True,
    )
    # 메시지 내용 * 메시지 형식에 따라 프론트에서 다르게 parsing
    message_content : str = models.TextField(
        verbose_name= "메시지 본문",
        blank = False,
        null = False,
        default = "",
    ),
    # 메시지가 존재하는 채팅방
    room_id : int = models.PositiveIntegerField(
        verbose_name= "메시지가 속한 채팅방 ID",
        default = None,
        blank = False,
        null = True,
        index = True,
    )
    # 메시지 보낸 유저
    created_by : int = models.PositiveIntegerField(
        verbose_name = "메시지 작성자",
        blank = False,
        null = True,
        default = None,
        index = True,
    )
