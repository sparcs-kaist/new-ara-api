from rest_framework import permissions
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.models.message import ChatMessage

# 채팅방 메시지 읽기 권한
class MessageReadPermissions(permissions.BasePermission):
    """
    메시지 읽기 권한
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # CREATE or LIST처럼 "chat_room"이 payload/query에만 있는 경우
        chat_room_id = request.data.get('chat_room') or request.query_params.get('chat_room')

        # retrieve/update/destroy 시에는 메시지 인스턴스에서 chat_room 가져오기
        if view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            message = view.get_object()
            chat_room_id = message.chat_room_id

        # chat_room_id가 없는 경우(예: 전체 메시지 목록?)
        if not chat_room_id:
            return True

        membership = ChatRoomMemberShip.objects.filter(
            chat_room_id=chat_room_id,
            user=request.user
        ).first()

        return membership and membership.role not in [
            ChatUserRole.BLOCKED.value,
            ChatUserRole.BLOCKER.value,
        ]

# 메시지 작성 : 참여자 이상
class MessageWritePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        chat_room_id = request.data.get('chat_room')
        if not chat_room_id:
            return False
        
        membership = ChatRoomMemberShip.objects.filter(
            chat_room_id=chat_room_id,
            user=request.user
        ).first()

        return membership and membership.role not in [
            ChatUserRole.BLOCKED.value,
            ChatUserRole.BLOCKER.value,
            ChatUserRole.OBSERVER.value,
        ]

# 메시지 삭제 권한 : 본인 메시지 or 관리자 이상
class MessageDeletePermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        message = obj  # ChatMessage 인스턴스
        # 본인이 작성한 메시지이거나, 관리자인 경우 허용
        is_owner = (message.created_by == request.user)
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
class MessageUpdatePermissions(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        message = obj  # ChatMessage 인스턴스
        is_owner = message.created_by == request.user
        
        return is_owner