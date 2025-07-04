from rest_framework import (
    permissions,
    response,
    status,
    viewsets,
)
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.message import ChatMessage
from apps.chatting.models.room import ChatRoom
from apps.chatting.serializers.message import (
    MessageSerializer,
    MessageCreateSerializer, 
    MessageUpdateSerializer,
    MessageDeleteResponseSerializer
)
from apps.chatting.permissions.message import (
    MessageReadPermissions,
    MessageWritePermissions,
    MessageDeletePermissions,
    MessageUpdatePermissions,
)

@extend_schema_view(
    list=extend_schema(
        description="채팅방의 메시지 목록 조회"
    ),
    create=extend_schema(
        description="새 메시지 작성"
    ),
    retrieve=extend_schema(
        description="특정 메시지 조회"
    ),
    update=extend_schema(
        description="메시지 수정"
    ),
    partial_update=extend_schema(
        description="메시지 부분 수정"
    ),
    destroy=extend_schema(
        responses={200: MessageDeleteResponseSerializer},
        description="메시지 삭제"
    ),
)
class ChatMessageViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    serializer_class = MessageSerializer
    
    action_permission_classes = {
        "list": (permissions.IsAuthenticated, MessageReadPermissions,),
        "retrieve": (permissions.IsAuthenticated, MessageReadPermissions,),
        "create": (permissions.IsAuthenticated, MessageWritePermissions,),
        "update": (permissions.IsAuthenticated, MessageUpdatePermissions,),
        "partial_update": (permissions.IsAuthenticated, MessageUpdatePermissions,),
        "destroy": (permissions.IsAuthenticated, MessageDeletePermissions,),
    }
    
    action_serializer_class = {
        "create": MessageCreateSerializer,
        "update": MessageUpdateSerializer,
        "partial_update": MessageUpdateSerializer,
    }

    def get_queryset(self):
        """
        특정 채팅방의 메시지만 조회
        URL에서 room_id를 가져와서 필터링
        """
        room_id = self.kwargs.get('room_pk')
        if room_id:
            return ChatMessage.objects.filter(
                chat_room_id=room_id
            ).order_by('-created_at')
        return ChatMessage.objects.none()
    
    def get_room(self):
        """
        현재 채팅방 객체 반환 (권한 체크용)
        """
        room_id = self.kwargs.get('room_pk')
        return get_object_or_404(ChatRoom, id=room_id)

    def perform_create(self, serializer):
        """
        메시지 생성 시 채팅방과 작성자 자동 설정
        """
        room = self.get_room()
        serializer.save(
            chat_room=room,
            created_by=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        """
        메시지 삭제 (소프트 삭제)
        """
        instance = self.get_object()
        # 소프트 삭제 수행
        instance.delete()
        
        return response.Response(
            {"message": "메시지가 삭제되었습니다."},
            status=status.HTTP_200_OK
        )