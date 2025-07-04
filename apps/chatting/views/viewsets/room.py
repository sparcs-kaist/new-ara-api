from rest_framework import (
    decorators,
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, extend_schema_view

from datetime import timezone

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.room import ChatRoom
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.serializers.room import  ChatRoomCreateSerializer
from apps.chatting.permissions.room import RoomReadPermission, RoomBlockPermission, RoomDeletePermission, RoomLeavePermission

# chat/room 엔드포인트의 PATCH, PUT 비활성화
@extend_schema_view(
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
)

class ChatRoomViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    action_permission_classes = {
        "create": (permissions.IsAuthenticated,),
        "destroy": (RoomDeletePermission,),
        "leave": (permissions.IsAuthenticated, RoomLeavePermission),
        "read": (permissions.IsAuthenticated, RoomReadPermission),
        "block": (permissions.IsAuthenticated, RoomBlockPermission),
        "blocked": (permissions.IsAuthenticated,),
    }

    action_serializer_class = {
        "create": ChatRoomCreateSerializer,
        "leave": ChatRoomCreateSerializer,
        "read": ChatRoomCreateSerializer,
        "block": ChatRoomCreateSerializer,
        "blocked": ChatRoomCreateSerializer,
    }

    method_permission_classes = {
        "POST": (permissions.IsAuthenticated,), # 채팅방 생성 권한 : 모든 로그인 된 User
        "DELETE": (RoomDeletePermission,)
    }

    method_serializer_class = {
        "POST": ChatRoomCreateSerializer,
    }

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()

        # 부속 데이터 먼저 정리
        ChatRoomMemberShip.objects.filter(chat_room=room).delete() #User의 Membership 삭제
        room.room_permission.delete()  #Room에 설정된 Permission도 삭제 (1:1 관계이므로 바로 삭제)

        room.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in self.action_permission_classes:
            return [perm() for perm in self.action_permission_classes[self.action]]
        
        if self.request.method in self.method_permission_classes:
            return [perm() for perm in self.method_permission_classes[self.request.method]]

        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in self.action_serializer_class:
            return self.action_serializer_class[self.action]

        if self.request.method in self.method_serializer_class:
            return self.method_serializer_class[self.request.method]

        return super().get_serializer_class()

    def get_queryset(self):
        # GET 요청시 : 자신과 관련된 채팅방만..
        if self.request.method == "GET":
            return ChatRoom.objects.filter(membership_info_set__user=self.request.user).distinct()
        return ChatRoom.objects.all()

    # chat/room/<roomid>/leave : 해당 room 나가기
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    # chat/room/<roomid>/read : 해당 room의 채팅방 읽음 처리
    # @Todo : last_seen_message_id 도 업데이트 해야한다.
    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.last_seen_at = timezone.now()
            membership.save()
        return response.Response(status=status.HTTP_200_OK)

    # chat/room/<roomid>/block : 해당 room 차단.
    @action(detail=True, methods=["patch"])
    def block(self, request, pk=None):
        room = self.get_object()
        
        # 명시적으로 "unblock"이 true일 때만 차단 해제, 그 외에는 항상 차단
        unblock = request.data.get("unblock", False)
        
        membership, created = ChatRoomMemberShip.objects.get_or_create(
            chat_room=room, 
            user=request.user
        )
        
        # unblock이 True일 때만 PARTICIPANT로 변경, 그 외에는 BLOCKER
        membership.role = ChatUserRole.PARTICIPANT.value if unblock else ChatUserRole.BLOCKER.value
        membership.save()
        
        return response.Response(status=status.HTTP_200_OK)

    # chat/room/<roomid>/unblock : 해당 room 차단 해제.
    @action(detail=True, methods=["patch"])
    def unblock(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership and membership.role == ChatUserRole.BLOCKER.value:
            # 차단 해제시 바로 참여자로 변경하면, 차단이 초대를 우회할 수 있으므로 방에서 나간것 처리 = 삭제
            membership.delete()
            return response.Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def blocked_list(self, request):
        blocked_rooms = ChatRoomMemberShip.get_blocked_room_list(request.user)
        serializer = self.get_serializer(blocked_rooms, many=True)
        return response.Response(serializer.data)
