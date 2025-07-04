from rest_framework import (
    permissions,
    response,
    status,
    viewsets,
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.message import ChatMessage
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
    list=extend_schema(description="메시지 목록 조회 (필요시 query/filter 사용)"),
    create=extend_schema(description="새 메시지 작성"),
    retrieve=extend_schema(description="특정 메시지 조회"),
    update=extend_schema(description="메시지 수정"),
    partial_update=extend_schema(description="메시지 부분 수정"),
    destroy=extend_schema(
        responses={200: MessageDeleteResponseSerializer},
        description="메시지 삭제"
    ),
)
class ChatMessageViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    """
    /api/chat/messages/  - Payload로 chat_room을 포함해 메시지 생성
    """
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
        # 모든 메시지 또는 필요시 query param으로 필터
        return ChatMessage.objects.all()

    def perform_create(self, serializer):
        """
        메시지 생성 시 작성자만 자동 설정 (chat_room은 payload로 받음)
        """
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        메시지 삭제
        """
        instance = self.get_object()
        instance.delete()  # 소프트 삭제가 아니라면 일반 delete()
        return response.Response({"message": "메시지가 삭제되었습니다."}, status=status.HTTP_200_OK)