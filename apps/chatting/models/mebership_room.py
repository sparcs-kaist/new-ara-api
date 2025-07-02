from enum import Enum
import datetime

from django.conf import settings
from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom

# 각각의 채팅방에서 사용자의 역할
class ChatUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    OBSERVER = "OBSERVER"        # 관전자 - 채팅을 볼 수만 있는 사람
    BLOCKED = "BLOCKED"          # 차단됨 - 채팅방에서 차단된 사람
    BLOCKER = "BLOCKER"         # 채팅방을 차단한 사람 (초대 거부)

class ChatNameType(str, Enum):
    NICKNAME = "NICKNAME"  # 닉네임
    ANONYMOUS = "ANONYMOUS"  # 익명
    REAL_NAME = "REAL_NAME"  # 실명

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoomMemberShip(MetaDataModel):
    # User ID
    user_id = models.ForeignKey(
        verbose_name="User 정보",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="room_participant_set",
        db_index=True,
    )
    # 해당 User가 참여하고 있는 채팅방 ID
    chat_room = models.ForeignKey(
        verbose_name="room_id",
        to=ChatRoom,
        on_delete=models.CASCADE,
        related_name="membership_info_set",
        db_index=True,
    )
    # User의 채팅방에서의 역할
    role : ChatUserRole = models.CharField(
        verbose_name= "role",
        max_length = 20,
        choices = [(role.value, role.name) for role in ChatUserRole],
        default = ChatUserRole.PARTICIPANT.value,
    )
    # 채팅방에서 이름 표시 방식
    chat_name_type : str = models.CharField(
        verbose_name= "chat_name_type",
        max_length = 20,
        choices= [(name_type.value, name_type.name) for name_type in ChatNameType],
        default = ChatNameType.NICKNAME.value,
        blank = False,
        null = False,
    )
    # 마지막 채팅방 접속 일시
    last_seen_at : models.DateTimeField = models.DateTimeField(
        verbose_name = "last_seen_at",
        null = True,
        blank = False,
        auto_now = True,
        default = None
    )
    last_seen_message_id : int = models.PositiveIntegerField(
        verbose_name= "last_seen_message_id",
        default = None,
        blank = False,
        null = True,
    )
    #채팅방 알림 설정 여부
    subscribed : bool = models.BooleanField(
        verbose_name= "subscribed",
        default = True,
        blank = False,
        null = True,
    )

    # created_at : 채팅방에 참여시
    # deleted_at : 채팅방에서 나갔을 때 (완전히 다시 참여할 수 없는 것은 아니므로 soft delete를 이용!)