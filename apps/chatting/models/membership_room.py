from enum import Enum
import datetime

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import Max, Q
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom, ChatRoomType, ChatNameType
from apps.chatting.models.message import ChatMessage

# 각각의 채팅방에서 사용자의 역할
class ChatUserRole(str, Enum):
    OWNER = "OWNER"              # 소유자 - 채팅방 최고 관리자 처음에는 생성자.
    ADMIN = "ADMIN"              # 관리자 - 채팅방 관리 권한을 가진 사람
    PARTICIPANT = "PARTICIPANT"   # 참여자 - 채팅에 참여할 수 있는 사람
    BLOCKED = "BLOCKED"          # 차단됨 - 채팅방에서 차단된 사람
    BLOCKER = "BLOCKER"         # 채팅방을 차단한 사람 (초대 거부)

# 각각의 유저가 참여하고 있는 채팅방 정보
class ChatRoomMemberShip(MetaDataModel):
    # User object
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
    )
    # 여러 사용자가 같은 "마지막으로 본 메시지"를 가리킬 수 있어야 하므로 FK로 정의한다.
    last_seen_message = models.ForeignKey(
        ChatMessage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_last_seen_message'
    )
    #채팅방 알림 설정 여부
    subscribed : bool = models.BooleanField(
        verbose_name= "subscribed",
        default = False,
        blank = False,
        null = True,
    )
    # 방 안에서 구분되는 익명 번호 (방장 0, 익명1, 익명2 ...). 다시 들어와도 유지
    anon_number = models.PositiveIntegerField(
        verbose_name = "익명 번호",
        null = True,
        blank = True,
        default = None,
    )

    # created_at : 채팅방에 참여시
    # deleted_at : 채팅방에서 나갔을 때 (완전히 다시 참여할 수 없는 것은 아니므로 soft delete를 이용!)

    def save(self, *args, **kwargs):
        if self.anon_number is None:
            # 같은 방에 동시에 들어와도 번호가 겹치지 않게 방을 잠그고 번호를 정한다
            with transaction.atomic():
                list(ChatRoom.objects.select_for_update().filter(pk=self.chat_room_id).values_list("pk", flat=True))
                self.anon_number = self.pick_anon_number()
                super().save(*args, **kwargs)
            return
        super().save(*args, **kwargs)

    def pick_anon_number(self) -> int:
        room_memberships = ChatRoomMemberShip.objects.queryset_with_deleted.filter(
            chat_room_id=self.chat_room_id,
        ).exclude(pk=self.pk)

        # 예전에 있던 유저면 그때 번호
        previous = room_memberships.filter(
            user_id=self.user_id,
            anon_number__isnull=False,
        ).values_list("anon_number", flat=True).first()
        if previous is not None:
            return previous

        if self.role == ChatUserRole.OWNER.value:
            return 0

        last = room_memberships.aggregate(last=Max("anon_number"))["last"]
        return (last or 0) + 1

    # 방의 이름 표시 방식(chat_name_type)이 적용된 이름
    def get_display_name(self) -> str:
        name_type = self.chat_room.chat_name_type

        if name_type == ChatNameType.ANONYMOUS.value:
            if self.role == ChatUserRole.OWNER.value:
                return "방장"
            # 번호가 생기기 전의 기존 멤버 (다음 저장 때 번호를 받는다)
            if self.anon_number is None:
                return "익명"
            return f"익명{self.anon_number}"

        profile = getattr(self.user, "profile", None)
        if profile is None:
            return self.user.username
        if name_type == ChatNameType.REAL_NAME.value:
            return profile.realname
        return profile.nickname

    # 차단 관계가 아닌 멤버십. 없으면 None
    @classmethod
    def get_active(cls, chat_room, user):
        return cls.objects.filter(
            chat_room=chat_room,
            user=user,
        ).exclude(
            role__in=[ChatUserRole.BLOCKED.value, ChatUserRole.BLOCKER.value],
        ).first()

    @classmethod
    def is_dm_exist(cls, user1, user2) -> bool:
        return ChatRoom.objects.filter(
            room_type=ChatRoomType.DM.value,
            membership_info_set__user=user1
        ).filter(
            membership_info_set__user=user2
        ).exists()
    
    #User의 DM을 Block 설정 하는 경우
    @transaction.atomic
    @classmethod
    def block_dm(cls, blocker, blocked) -> None:
        dm_room = ChatRoom.objects.filter(
            Q(membership_info_set__user=blocker) & Q(membership_info_set__user=blocked),
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
        dm_room = ChatRoom.objects.filter(
            Q(membership_info_set__user=blocker) & Q(membership_info_set__user=blocked),
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

    
    # 차단한 user_list 조회
    # user가 차단한 리스트를 조회한다.
    @classmethod
    def get_block_user_list(cls, user) -> list:
        return cls.objects.filter(
            user=user,
            role=ChatUserRole.BLOCKER.value
        )

    # 차단한 채팅방 list 조회
    # dm_room과 group_room을 모두 포함한다.
    @classmethod
    def get_blocked_room_list(cls, user) -> list:
        return ChatRoom.objects.filter(
            Q(membership_info_set__user=user) & Q(membership_info_set__role=ChatUserRole.BLOCKER.value)
        )
    
    # 차단한 group_room (그룹채팅, 오픈 채팅) 방 리스트 조회
    @classmethod
    def get_blocked_group_room_list(cls, user) -> list:
        return ChatRoom.objects.filter(
            Q(membership_info_set__user=user) & Q(membership_info_set__role=ChatUserRole.BLOCKER.value),
            room_type__in=[ChatRoomType.GROUP_DM.value, ChatRoomType.OPEN_CHAT.value],
        )