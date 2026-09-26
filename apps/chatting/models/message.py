from enum import Enum
from datetime import timedelta
from urllib.parse import urlparse
import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoomType

class ChatMessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    EMOTICON = "EMOTICON"
    VOTE = "VOTE"
    PAYMENT_REQUEST = "PAYMENT_REQUEST"
    DELIVERY_ORDER = "DELIVERY_ORDER"
    DELIVERY_ARRIVAL = "DELIVERY_ARRIVAL"
    SYSTEM = "SYSTEM"

USER_SENDABLE_MESSAGE_TYPES = {
    ChatMessageType.TEXT.value,
    ChatMessageType.IMAGE.value,
    ChatMessageType.FILE.value,
    ChatMessageType.EMOTICON.value,
}

# 배달 주문은 주문 취소로만 없앤다
DELETABLE_MESSAGE_TYPES = USER_SENDABLE_MESSAGE_TYPES | {
    ChatMessageType.VOTE.value,
    ChatMessageType.PAYMENT_REQUEST.value,
}

DELIVERY_ONLY_MESSAGE_TYPES = {
    ChatMessageType.DELIVERY_ORDER.value,
    ChatMessageType.DELIVERY_ARRIVAL.value,
}

MESSAGE_LIFETIME = timedelta(days=30)

class ChatMessage(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        # 방의 메시지를 최신순으로 읽는 쿼리 (chat_room = ? AND deleted_at = ? ORDER BY id DESC)
        indexes = [
            models.Index(fields=["chat_room", "deleted_at", "id"], name="chat_msg_room_deleted_id"),
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
    # 메시지 보낸 유저 (SYSTEM 메시지는 작성자가 없다)
    created_by = models.ForeignKey(
        verbose_name="메시지 작성자",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_set",
        db_index=True,
        null=True,
        blank=True,
    )
    #메시지 만료 시점
    expired_at = models.DateTimeField(
        verbose_name = "메시지 만료 시점",
        null = True,
        blank = False,
        auto_now = False,
        default = None
    )

    def clean(self):
        super().clean()

        if self.message_type in DELIVERY_ONLY_MESSAGE_TYPES and \
                self.chat_room.room_type != ChatRoomType.DELIVERY.value:
            raise ValidationError({"message_type": "함께 배달 방에서만 보낼 수 있는 메시지입니다."})

        if self.message_type == ChatMessageType.SYSTEM.value and self.created_by_id is not None:
            raise ValidationError({"created_by": "SYSTEM 메시지는 작성자가 없어야 합니다."})

        if self.message_type != ChatMessageType.SYSTEM.value and self.created_by_id is None:
            raise ValidationError({"created_by": "메시지 작성자가 필요합니다."})

        if self.message_type in [ChatMessageType.IMAGE.value, ChatMessageType.FILE.value]:
            # URL에 쿼리스트링이 있을 수 있으므로 path만 추출
            parsed_url = urlparse(self.message_content)
            # 추출한 path에서 확장자만 분리 (예: '.jpg', '.svg')
            ext = os.path.splitext(parsed_url.path)[1].lower()

            allowed_image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            allowed_file_exts = allowed_image_exts | {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                '.ppt', '.pptx', '.zip', '.tar', '.gz', '.mp4', '.mp3'
            }

            if self.message_type == ChatMessageType.IMAGE.value and ext not in allowed_image_exts:
                raise ValidationError({"message_content": f"허용되지 않은 이미지 확장자입니다: {ext or '확장자 없음'}"})

            if self.message_type == ChatMessageType.FILE.value and ext not in allowed_file_exts:
                raise ValidationError({"message_content": f"허용되지 않은 파일 확장자입니다: {ext or '확장자 없음'}"})

    # created_at : 메시지 작성 일시
    # updated_at : 메시지가 수정되었을 때
    # deleted_at : 메시지가 (사용자에 의해) 삭제되었을 때. (아직 백업 테이블로 이동 X)

    @classmethod
    @transaction.atomic
    def create(cls, **kwargs):
        # chat_room 확인
        chat_room = kwargs.get('chat_room')
        if not chat_room:
            raise ValueError("chat_room is missing.")

        kwargs.setdefault('expired_at', timezone.now() + MESSAGE_LIFETIME)

        # 메시지 생성
        instance = cls(**kwargs)
        instance.full_clean() #full clean 호출시 clean()도 호출됨
        instance.save()

        # 방의 최근 메시지 정보 업데이트
        chat_room.recent_message = instance
        chat_room.recent_message_at = timezone.now()
        chat_room.save(update_fields=["recent_message", "recent_message_at", "updated_at"])

        return instance

    @classmethod
    def create_system(cls, chat_room, content: str):
        return cls.create(
            chat_room=chat_room,
            message_type=ChatMessageType.SYSTEM.value,
            message_content=content,
            created_by=None,
        )
