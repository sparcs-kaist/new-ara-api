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
    permission_classes = [RoomReadPermission]
    
    action_permission_classes = {
        "leave": (permissions.IsAuthenticated, RoomLeavePermission),
        "read": (permissions.IsAuthenticated, RoomReadPermission),
        "block": (permissions.IsAuthenticated, RoomBlockPermission),
        "blocked": (permissions.IsAuthenticated,),
    }

    action_serializer_class = {
        "leave": ChatRoomCreateSerializer,
        "read": ChatRoomCreateSerializer,
        "block": ChatRoomCreateSerializer,
        "blocked": ChatRoomCreateSerializer,
    }

    def get_queryset(self):
        """자신이 참여한 방만"""
        return ChatRoom.objects.filter(memberships__user=self.request.user).distinct()

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.last_seen_at = timezone.now()
            membership.save()
        return response.Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def block(self, request, pk=None):
        room = self.get_object()
        block = request.data.get("block", True)
        membership, created = ChatRoomMemberShip.objects.get_or_create(chat_room=room, user=request.user)
        membership.role = ChatUserRole.BLOCKER.value if block else ChatUserRole.PARTICIPANT.value
        membership.save()
        return response.Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def blocked(self, request):
        blocked_rooms = ChatRoomMemberShip.get_blocked_room_list(request.user)
        serializer = self.get_serializer(blocked_rooms, many=True)
        return response.Response(serializer.data)
