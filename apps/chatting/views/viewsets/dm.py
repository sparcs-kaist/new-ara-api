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
from django.db import IntegrityError

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
        "create": (permissions.IsAuthenticated, CreateDMPermission,),
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
    
    # dm/ POST: DM 방 만들기 - 기존 메서드 활용
    def create(self, request, *args, **kwargs):
        # 이미 존재하는 DM인 경우 : permission에서 block
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 대화 상대 ID
        dm_to = serializer.validated_data['dm_to']
        
        # 새 DM 생성
        user_nickname = request.user.profile.nickname
        dm_to_nickname = dm_to.profile.nickname
        dm_room = ChatRoom.objects.create(
            room_type=ChatRoomType.DM.value,
            room_title=f"DM_{user_nickname},{dm_to_nickname}",
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
            DMSerializer(dm_room, context={'request': request}).data,
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
    
    # dm/block PATCH: DM 차단하기 - block_dm 메서드 활용
    @action(detail=True, methods=["patch"])
    def block(self, request, pk=None):
        dm_room = self.get_object()
        
        # 상대방 찾기
        other_user = dm_room.membership_info_set.exclude(user=request.user).first()
        if not other_user:
            return response.Response(
                {"error": "DM 상대방을 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 차단 처리 - 모델 메서드 활용
        try:
            ChatRoomMemberShip.block_dm(request.user, other_user.user)
            return response.Response(status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # dm/unblock PATCH: DM 차단 해제하기 - unblock_dm 메서드 활용
    @action(detail=True, methods=["patch"])
    def unblock(self, request, pk=None):
        dm_room = self.get_object()
        
        # 상대방 찾기
        other_user = dm_room.membership_info_set.exclude(user=request.user).first()
        if not other_user:
            return response.Response(
                {"error": "DM 상대방을 찾을 수 없습니다."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 차단 해제 처리 - 모델 메서드 활용
        try:
            ChatRoomMemberShip.unblock_dm(request.user, other_user.user)
            return response.Response(status=status.HTTP_200_OK)
        except IntegrityError as e:
            return response.Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )