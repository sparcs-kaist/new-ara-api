from enum import Enum
import datetime

from django.conf import settings
from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom, ChatRoomType
from apps.chatting.models.message import ChatMessage

# 각각의 채팅방에서 사용자의 역할
class ChatUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    OBSERVER = "OBSERVER"        # 관전자 - 채팅을 볼 수만 있는 사람
    BLOCKED = "BLOCKED"          # 차단됨 - 채팅방에서 차단된 사람
    BLOCKER = "BLOCKER"         # 채팅방을 차단한 사람 (초대 거부)

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoomMemberShip(MetaDataModel):
    # User ID
    user = models.ForeignKey(
        verbose_name="User 정보",
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="room_participant_set",
        db_index=True,
    )
    # 해당 User가 참여하고 있는 채팅방 ID
    chat_room = models.ForeignKey(
        verbose_name="chat_room",
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
    # 마지막 채팅방 접속 일시
    last_seen_at : models.DateTimeField = models.DateTimeField(
        verbose_name = "last_seen_at",
        null = True,
        blank = False,
        auto_now = True,
        default = None
    )
    last_seen_message = models.OneToOneField(
        ChatMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_last_seen_message'
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

    @classmethod
    def is_dm_exist(cls, user1, user2) -> bool:
        # 두 유저 동시 참여 & 채팅방 타입 DM 존재 조회
        return ChatRoom.objects.filter(
            membership_info_set__user=user1,
            membership_info_set__user=user2,
            room_type=ChatRoomType.DM.value
        ).exists()
    
    #User의 DM을 Block 설정 하는 경우
    @transaction.atomic
    @classmethod
    def block_dm(cls, blocker, blocked) -> None:
        dm_room = ChatRoom.objects.filter(
            membership_info_set__user=blocker,
            membership_info_set__user=blocked,
            room_type=ChatRoomType.DM.value
        ).first()

        # 이미 채팅방이 존재하는 경우
        if dm_room:
            blocker_membership = dm_room.membership_info_set.filter(user=blocker).first()
            blocker_membership.role = ChatUserRole.BLOCKER.value
            blocker_membership.save()

            blocked_membership = dm_room.membership_info_set.filter(user=blocked).first()
            blocked_membership.role = ChatUserRole.BLOCKED.value
            blocked_membership.save()

        # 채팅방이 존재하지 않은 경우 차단 처리
        else:
            dm_room = ChatRoom.objects.create(
                room_type=ChatRoomType.DM.value
            )
            
            blocker_membership = ChatRoomMemberShip.objects.create(
                user=blocker,
                role=ChatUserRole.BLOCKER.value,
                chat_room=dm_room #dm_room 에도 자동 반영
            )
            
            blocked_membership = ChatRoomMemberShip.objects.create(
                user=blocked,
                role=ChatUserRole.BLOCKED.value,
                chat_room=dm_room #dm_room 에도 자동 반영
            )

    #User의 Unblock 설정
    @transaction.atomic
    @classmethod
    #blocker : 자신이 block한 사람을 차단 해제 하려는 User
    #blocked : blocked 된 User -> 차단 해제 대상
    def unblock_dm(cls, blocker, blocked) -> None:
        dm_room = ChatRoom.lojects.filter(
            membership_info_set__user=blocker,
            membership_info_set__user=blocked,
            room_type=ChatRoomType.DM.value
        ).first()

        # 채팅방이 존재하지 않는 경우 : (Blocked 되지 않은 경우임)
        if not dm_room:
            raise IntegrityError("차단되지 않은 User입니다.")

        # Blocked 상태에서 Unblock 상태로 변경
        blocker_membership = dm_room.membership_info_set.filter(user=blocker).first()
        blocker_membership.role = ChatUserRole.PARTICIPANT.value
        blocker_membership.save()

        blocked_membership = dm_room.membership_info_set.filter(user=blocked).first()
        blocked_membership.role = ChatUserRole.PARTICIPANT.value
        blocked_membership.save()