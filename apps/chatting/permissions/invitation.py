from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.models.room import ChatRoom

# 역할 상수 정리
ALLOWED_INVITATION_ROLES = [
    ChatUserRole.OWNER.value,
    ChatUserRole.ADMIN.value,
    ChatUserRole.PARTICIPANT.value,
]

BLOCK_ROLES = [
    ChatUserRole.BLOCKER.value,
    ChatUserRole.BLOCKED.value,
]


# 공통 유틸 함수
def get_membership(room, user):
    return ChatRoomMemberShip.objects.filter(
        chat_room=room,
        user=user
    ).first()


def is_blocked_or_blocker(membership):
    return membership and membership.role in BLOCK_ROLES


# 초대 생성 권한
class CreateInvitationPermission(permissions.BasePermission):
    """
    방 참여자만 초대 가능
    차단된 사람은 초대 불가
    """
    def has_permission(self, request, view):
        invited_room_id = request.data.get("invited_room")
        if not invited_room_id:
            return False  # 방 정보 없으면 권한 없음 처리

        try:
            room = ChatRoom.objects.get(pk=invited_room_id)
        except ChatRoom.DoesNotExist:
            return False

        membership = get_membership(room, request.user)

        invited_user_id = request.data.get("invitation_to")
        if invited_user_id:
            invited_membership = get_membership(room, invited_user_id)
            if is_blocked_or_blocker(invited_membership):
                return False

        return membership and membership.role in ALLOWED_INVITATION_ROLES

# 초대 삭제 권한 (거절과는 다름)
class DeleteInvitationPermission(permissions.BasePermission):
    """
    방 참여자만 삭제 가능
    차단 상태면 불가
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = get_membership(room, request.user)

        if is_blocked_or_blocker(membership):
            return False

        return membership and membership.role in ALLOWED_INVITATION_ROLES


# 초대 수락 권한 (초대 받은 사람만 가능)
class AcceptInvitationPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.invitation_to == request.user
        )


# 초대 거절 권한 (초대 받은 사람만 가능)
class RejectInvitationPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.invitation_to == request.user
        )

#자신의 초대장 조회 권한 : 로그인 한 User 라면 모두 가능