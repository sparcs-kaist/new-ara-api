from enum import Enum
from datetime import timezone

from django.conf import settings
from django.db import IntegrityError, models, transaction
from ara.db.models import MetaDataModel
from apps.chatting.models.room import ChatRoom
from apps.chatting.models.membership_room import ChatUserRole
from apps.chatting.models.membership_room import ChatRoomMemberShip

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

    # deleted_at : 초대장이 삭제 (취소) 되었을 때 (혹은 수락해서 요청이 완료되었을 때)
    # created_at : 초대장이 생성 되었을 때

    #초대장 유효성 검사
    def is_valid_invitation(self) -> bool :
        if self.expired_at is not None and self.expired_at < timezone.now():
            return False
        return True
    
    #초대장 수락
    @transaction.atomic
    def accept_invitation(self) -> None :
        # 초대장 유효성 검사
        if not self.is_valid_invitation():
            raise IntegrityError("초대장이 유효하지 않습니다.")
        # 자신이 Block한 채팅방인 경우
        if self.invited_room.membership_info_set.filter(user=self.invitation_to, role=ChatUserRole.BLOCKER).exists():
            raise IntegrityError("차단한 채팅방입니다.")
        #Block 당한 채팅방인 경우
        if self.invited_room.membership_info_set.filter(user=self.invitation_to, role = ChatUserRole.BLOCKED).exists():
            raise IntegrityError("차단된 채팅방입니다.")
        # 이미 참여한 채팅방인 경우
        if self.invited_room.membership_info_set.filter(user=self.invitation_to).exists():
            raise IntegrityError("이미 참여한 채팅방입니다.")
        
        # 초대장 수락 : ChatRoomMemberShip 객체 생성
        ChatRoomMemberShip.objects.create(
            user = self.invitation_to,
            chat_room = self.invited_room,
            role = self.invitation_role,
            subscribed = False, #처음 참여시 알림은 비활성화
            last_seen_at = timezone.now(), # 처음 참여 : 마지막 접속 일자는 현지
            last_seen_message = None,
        )

        #처리 완료된 초대장 삭제
        self.delete()

    # 초대장 거절 : 초대장 삭제
    def reject_invitation(self) -> None :
        self.delete()