from enum import Enum
import datetime

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

#User의 Type 별 권한 설정 테이블
class ChatRoomPermission(MetaDataModel):
    # permission이 적용될 채팅방 / 채팅방 하나당 하나의 Permission 존재 (1:1 realationship))
    chat_room = models.OneToOneField(
        verbose_name = "권한이 적용될 채팅방",
        to=ChatRoom,
        on_delete=models.CASCADE,
        related_name="room_permission",
        db_index=True,
    )
    # 입장 권한 (전체 or Invited)
    entrance_permission = models.CharField(
        verbose_name = "입장 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("INVITED", "초대받은 사용자만"),
        ],
        default = "INVITED",
        blank = False,
        null = False,
    )
    # 초대할 수 있는 사용자
    invite_permission = models.CharField(
        verbose_name = "초대 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자 이상"),
            ("OWNER", "소유자만"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    )
    # 메세지 보내기 권한
    message_permission = models.CharField(
        verbose_name = "메세지 보내기 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자 이상"),
            ("OWNER", "소유자만"),
            ("PARTICIPANT", "참여자 이상"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    )
    # 유저 강퇴 권한
    kick_permission = models.CharField(
        verbose_name = "유저 강퇴 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자 이상"),
            ("OWNER", "소유자만"),
            ("PARTICIPANT", "참여자 이상"),
        ],
        default = "ALL",
        blank = False,
        null = False,
    )
    permission_update_permmission = models.CharField(
        verbose_name = "권한 업데이트 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자 이상"),
            ("OWNER", "소유자만"),
        ],
        default = "OWNER",
        blank = False,
        null = False,
    )
    room_delete_permission = models.CharField(
        verbose_name = "채팅방 삭제 권한",
        max_length = 20,
        choices = [
            ("ALL", "전체"),
            ("ADMIN", "관리자 이상"),
            ("OWNER", "소유자만"),
            ("PARTICIPANT", "참여자 이상"),
        ],
        default = "OWNER",
        blank = False,
        null = False,
    )

    # created_at : 채팅방이 처음 생성될 때 같이 생성됨
    # deleted_at : 채팅방이 삭제될 때 같이 삭제됨

    # 권한 업데이트
    @transaction.atomic
    def update_permission(
        self,
        entrance : str = None,
        invite : str = None,
        message : str = None,
        kick : str = None,
        permission_update : str = None,
        delete_room : str = None,
    ):
        if entrance is not None:
            self.entrance_permission = entrance
        if invite is not None:
            self.invite_permission = invite
        if message is not None:
            self.messagee_permisson = message
        if kick is not None:
            self.kick_permission = kick
        if permission_update is not None:
            self.permission_update_permmission = permission_update
        if delete_room is not None:
            self.room_delete_permission = delete_room
        self.save()