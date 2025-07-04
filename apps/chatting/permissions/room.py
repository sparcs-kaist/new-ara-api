from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole


#채팅방 생성 : 모든 로그인한 User (IsAuthenticated)
    
#채팅방 삭제 : 채팅방 소유자 (Owner)만 가능
class RoomDeletePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()
        return membership and membership.role == ChatUserRole.OWNER.value
    
#채팅방 읽기 : 참여되어 있고, 차단되거나 차단하지 않은 채팅방만 가능
class RoomReadPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        return membership and \
            (membership.role != ChatUserRole.BLOCKED.value) and \
            (membership.role != ChatUserRole.BLOCKER.value)
    
#채팅방 나가기 : 소유자 제외 가능 (소유자는 권한 이전 이후 나가기 가능)   
class RoomLeavePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        return membership and membership.role != ChatUserRole.OWNER.value
    
#채팅방 차단 : BLOCKER, BLOCKED, OWNER일 경우 불가능
class RoomBlockPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()
        
        return membership and \
            (membership.role != ChatUserRole.BLOCKER.value) and \
            (membership.role != ChatUserRole.BLOCKED.value) and \
            (membership.role != ChatUserRole.OWNER.value)



#채팅방 차단 목록 조회 : IsAuthenticated