from rest_framework import (
    decorators,
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action
from django.db.models import Q

from drf_spectacular.utils import extend_schema, extend_schema_view

from django.utils import timezone

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.room import ChatRoom, ChatRoomType
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.serializers.dm import DMCreateSerializer, DMSerializer
from apps.chatting.permissions.dm import CreateDMPermission, LeaveDMPermission, BlockDMPermission, UnblockDMPermission


@extend_schema_view(
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
)
class DMViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = ChatRoom.objects.filter(room_type=ChatRoomType.DM.value)
    serializer_class = DMSerializer
    
    action_permission_classes = {
        "list": (permissions.IsAuthenticated,),
        "create": (permissions.IsAuthenticated, CreateDMPermission),
        "leave": (permissions.IsAuthenticated, LeaveDMPermission),
        "block": (permissions.IsAuthenticated, BlockDMPermission),
        "unblock": (permissions.IsAuthenticated, UnblockDMPermission),
    }
    
    action_serializer_class = {
        "create": DMCreateSerializer,
    }
    
    def get_queryset(self):
        # DM 목록 조회 시 자신이 참여한 DM만 조회
        if self.request.method == "GET":
            return ChatRoom.objects.filter(
                room_type=ChatRoomType.DM.value,
                membership_info_set__user=self.request.user
            ).distinct()
        return super().get_queryset()
    
    # dm/ POST: DM 방 만들기
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 대화 상대 ID
        dm_to = serializer.validated_data['dm_to']
        
        # 이미 존재하는 DM인지 확인
        existing_dm = ChatRoom.objects.filter(
            room_type=ChatRoomType.DM.value
        ).filter(
            Q(membership_info_set__user=request.user) & 
            Q(membership_info_set__user=dm_to)
        ).first()
        
        if existing_dm:
            # 이미 존재하는 경우 기존 DM 반환
            return response.Response(
                DMSerializer(existing_dm).data,
                status=status.HTTP_200_OK
            )
        
        # 새 DM 생성
        dm_room = ChatRoom.objects.create(
            room_type=ChatRoomType.DM.value,
            room_title=f"DM_{request.user.id}_{dm_to.id}",  # 내부 식별용
            created_by=request.user
        )
        
        # 두 사용자 모두 참가자로 추가
        ChatRoomMemberShip.objects.create(
            chat_room=dm_room, 
            user=request.user, 
            role=ChatUserRole.PARTICIPANT.value
        )
        
        ChatRoomMemberShip.objects.create(
            chat_room=dm_room, 
            user=dm_to, 
            role=ChatUserRole.PARTICIPANT.value
        )
        
        return response.Response(
            DMSerializer(dm_room).data,
            status=status.HTTP_201_CREATED
        )
    
    # dm/ DELETE: DM 방 나가기
    @action(detail=True, methods=["delete"])
    def leave(self, request, pk=None):
        dm_room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=dm_room, 
            user=request.user
        ).first()
        
        if membership:
            membership.delete()
        
        return response.Response(status=status.HTTP_204_NO_CONTENT)
    
    # dm/block PATCH: DM 차단하기
    @action(detail=True, methods=["patch"])
    def block(self, request, pk=None):
        dm_room = self.get_object()
        
        # 명시적으로 "unblock"이 true일 때만 차단 해제, 그 외에는 항상 차단
        unblock = request.data.get("unblock", False)
        
        membership, created = ChatRoomMemberShip.objects.get_or_create(
            chat_room=dm_room, 
            user=request.user
        )
        
        # 차단 또는 해제
        membership.role = ChatUserRole.PARTICIPANT.value if unblock else ChatUserRole.BLOCKER.value
        membership.save()
        
        return response.Response(status=status.HTTP_200_OK)
    
    # dm/unblock PATCH: DM 차단 해제하기
    @action(detail=True, methods=["patch"])
    def unblock(self, request, pk=None):
        dm_room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(
            chat_room=dm_room, 
            user=request.user
        ).first()
        
        if membership and membership.role == ChatUserRole.BLOCKER.value:
            membership.role = ChatUserRole.PARTICIPANT.value
            membership.save()
        
        return response.Response(status=status.HTTP_200_OK)