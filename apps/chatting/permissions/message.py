from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.models.message import ChatMessage

# 채팅방 메시지 읽기 권한
class MessageReadPermissions(permissions.BasePermissions):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        return membership and membership.role not in [
            chat_user_role.value for chat_user_role in [
                ChatUserRole.BLOCKED,
                ChatUserRole.BLOCKER,
            ]
        ]
    

# 메시지 작성 : 참여자 이상
class MessageWritePermissions(permissions.BasePermissions):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        room = view.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=room,
            user=request.user
        ).first()

        return membership and membership.role not in [
            chat_user_role.value for chat_user_role in [
                ChatUserRole.BLOCKED,
                ChatUserRole.BLOCKER,
                ChatUserRole.OBSERVER,
            ]
        ]
    
# 메시지 삭제 권한 : 본인 메시지 or 관리자 이상
class MessageDeletePermissions(permissions.BasePermissions):
    def has_object_permission(self, request, view):
        # obj는 ChatMessage 인스턴스여야 함
        if not request.user.is_authenticated:
            return False

        message = view.get_object() #ChatMessage 인스턴스
        # 본인이 작성한 메시지이거나, (추가: 관리자인 경우 허용)
        is_owner = message.created_by == request.user
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=message.chat_room,
            user=request.user
        ).first()
        is_admin = membership and membership.role in [
            ChatUserRole.OWNER.value,
            ChatUserRole.ADMIN.value,
        ]

        return is_owner or is_admin

# 메시지 수정 권한 : only 본인 메시지
class MessageUpdatePermissions(permissions.BasePermissions):
    def has_object_permission(self, request, view):
        # obj는 ChatMessage 인스턴스여야 함
        if not request.user.is_authenticated:
            return False

        message = view.get_object() #ChatMessage 인스턴스
        # 본인이 작성한 메시지이거나, (추가: 관리자인 경우 허용)
        is_owner = message.created_by == request.user
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=message.chat_room,
            user=request.user
        ).first()

        return is_owner