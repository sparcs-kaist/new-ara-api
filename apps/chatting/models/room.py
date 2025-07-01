from enum import Enum
import datetime

from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel

# 각각의 채팅방에서 사용자의 역할
class ChatUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    OBSERVER = "OBSERVER"        # 관전자 - 채팅을 볼 수만 있는 사람

class ChatNameType(str, Enum):
    NICKNAME = "NICKNAME"  # 닉네임
    ANOUNYMOUS = "ANONYMOUS"  # 익명
    REAL_NAME = "REAL_NAME"  # 실명

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoomMemberShip(MetaDataModel):
    # User ID
    user_id : int = models.PositiveIntegerField(
        verbose_name = "user_id",
        default = 0,
        index = True,
    )
    # 해당 User가 참여하고 있는 채팅방 ID
    room_id : int = models.PositiveIntegerField(
        verbose_name = "room_id",
        default = 0,
        index = True,
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
    #채팅방 알림 설정 여부
    subscribed : bool = models.BooleanField(
        verbose_name= "subscribed",
        default = True,
        blank = False,
        null = True,
    )