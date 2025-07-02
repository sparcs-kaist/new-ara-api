from enum import Enum
import datetime

from django.conf import settings
from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom

# 초대장에서 부여받을 사용자의 역할
class ChatInvitedUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    OBSERVER = "OBSERVER"        # 관전자 - 채팅을 볼 수만 있는 사람

class ChatRoomInvitation(MetaDataModel):
    # 초대받은 채팅방
    invited_room = models.ForeignKey(
        verbose_name = "초대된 채팅방",
        to = ChatRoom,
        on_delete = models.CASCADE,
        realted_name = "invitation_set",
        db_index = True,
    )
    # 초대받은 유저의 ID
    invitation_to = models.ForeignKey(
        verbose_name="초대받은 유저의 ID",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invited_set",
        db_index=True,
    )
    # 초대한 유저의 ID
    invitation_from  = models.ForeignKey(
        verbose_name="초대한 유저의 ID",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inviting_set",
        db_index=True,
    )
    # 초대받은 User가 부여받을 Role
    invitation_role : ChatInvitedUserRole = models.CharField(
        verbose_name= "초대받은 User의 Role",
        max_length = 20,
        choices= [(role.value, role.name) for role in ChatInvitedUserRole],
        default= ChatInvitedUserRole.PARTICIPANT.value,
        blank = False,
        null = False,
    )
    # 초대장 만료 시점
    expired_at = models.DateTimeField(
        verbose_name = "초대장 만료 일시",
        null = True,
        blank = False,
        auto_now = False,
        default = None,
    )

    # deleted_at : 초대장이 삭제 (취소) 되었을 때
    # created_at : 초대장이 생성 되었을 때
    