from enum import Enum
import datetime

from django.conf import settings
from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom

class ChatMessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    EMOTICON = "EMOTICON"

#ChatMessage 모델과 동일하게 쓰이나, 쿼리 성능 향상을 위해 만료된 메세지를 백업용으로만 쓴다.
class ExpiredChatMessage(MetaDataModel):
    # 메시지의 종류
    message_type : ChatMessageType = models.CharField(
        max_length = 20,
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
    room_id = models.ForeignKey(
        verbose_name= "메시지가 속한 채팅방 ID",
        to=ChatRoom,
        on_delete=models.CASCADE,
        related_name="expired_message_set",
        db_index=True,
    )
    # 메시지 보낸 유저
    created_by = models.ForeignKey(
        verbose_name="메시지 작성자",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_set",
        db_index=True,
    )

    # created_at : 메시지 데이터가 백업 데이터 테이블로 이동한 일시
    # deleted_at : 메시지가 완전히 삭제된 시간 (이 작업은 hard-delete 이므로 사실상 이 필드는 쓰이지 않음)
