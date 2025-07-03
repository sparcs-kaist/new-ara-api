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

class ChatMessage(MetaDataModel):
    # 유니크 순서쌍 정의
    class Meta:
        constraints = [
            models.UniqueConstraint(fields = ['chat_room', 'message_id'], name = 'unique_chatroom_messageid')
        ]
    
    # 메시지의 종류
    message_type : ChatMessageType = models.CharField(
        max_length = 20,
        choices = [(msg_type.value, msg_type.name) for msg_type in ChatMessageType],
        default = ChatMessageType.TEXT.value,
        verbose_name = "message_type",
        blank = False,
        null = False,
    )
    # 메시지의 고유 ID (chat_room, message_id) 순서쌍은 unique
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
    )
    # 메시지가 존재하는 채팅방
    chat_room = models.ForeignKey(
        verbose_name= "메시지가 속한 채팅방",
        to="chatting.ChatRoom", # 순환 참조 막기 위해 문자열 참조로 우회
        on_delete=models.CASCADE,
        related_name="message_set",
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
    #메시지 만료 시점
    expired_at = models.DateTimeField(
        verbose_name = "메시지 만료 시점",
        null = True,
        blank = False,
        auto_now = False,
        default = None
    )

    # created_at : 메시지 작성 일시
    # updated_at : 메시지가 수정되었을 때
    # deleted_at : 메시지가 (사용자에 의해) 삭제되었을 때. (아직 백업 테이블로 이동 X)

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        # race_condition 방지: 해당 채팅방의 메시지 row에 락을 걸고 가장 큰 message_id를 가져옴
        chat_room = kwargs.get('chat_room')
        if not chat_room:
            raise ValueError("chat_room is missing.")

        last_message = cls.objects.select_for_update().filter(chat_room=chat_room).order_by('-message_id').first()
        kwargs['message_id'] = (last_message.message_id if last_message else 0) + 1

        return super().create(**kwargs)

