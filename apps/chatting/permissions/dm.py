from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole, ChatRoom, ChatRoomType
from django.db.models import Q

#DM 생성 권한 - 이미 만들어진 방이 없고, 차단 상태가 아닌 경우
class CreateDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        dm_to = request.data.get("target_user")
        if not dm_to:   
            return False
        #두 User 사이에 이미 만들어진 DM 방이 있는지 확인
        existing_dm = ChatRoom.objects.filter(
        room_type=ChatRoomType.DM.value
        ).filter(
            Q(membership_info_set__user=request.user) & Q(membership_info_set__user_id=dm_to)
        ).exists()
        if existing_dm:
            return False
        return True

#DM 떠나기 권한 - 이미 방에 참여중, 차단 상태가 아닌 경우
class LeaveDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        # 참여 중인 방이면서 차단 상태가 아닌 경우
        return membership and membership.role not in [
            ChatUserRole.BLOCKED.value,
            ChatUserRole.BLOCKER.value,
        ]

#DM 차단 권한 - 차단 상태가 아닌 경우
class BlockDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        # membership이 없거나(방이 없거나 참여하지 않은 경우) 차단 상태가 아닌 경우
        return (membership is None) or (
            membership.role not in [
                ChatUserRole.BLOCKED.value,
                ChatUserRole.BLOCKER.value,
            ]
        )
    
#DM 차단 해제 권한 - 해당 user가 이미 차단 상태인 경우
class UnblockDMPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        # 이미 차단 상태인 경우에만 차단 해제 가능
        return membership and membership.role == ChatUserRole.BLOCKER.value
