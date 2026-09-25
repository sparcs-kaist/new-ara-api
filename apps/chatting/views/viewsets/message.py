from rest_framework import (
    permissions,
    response,
    status,
    viewsets,
)
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes
)

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.message import ChatMessage, DELETABLE_MESSAGE_TYPES
from apps.chatting.realtime import broadcast_room_update
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.serializers.message import (
    attachment_related_names,
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
        description="메시지 목록 조회 (필요시 query/filter 사용)",
        parameters=[
            OpenApiParameter(
                name='chat_room',
                description='필터링할 채팅방 ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            )
        ]
    ),
    create=extend_schema(description="새 메시지 작성"),
    retrieve=extend_schema(description="특정 메시지 조회"),
    update=extend_schema(description="메시지 수정"),
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
        "destroy": (permissions.IsAuthenticated, MessageDeletePermissions,),
    }
    
    action_serializer_class = {
        "create": MessageCreateSerializer,
        "update": MessageUpdateSerializer,
    }

    def get_queryset(self):
        # 내가 참여한(차단 관계가 아닌) 방의 메시지만
        my_room_ids = ChatRoomMemberShip.objects.filter(
            user=self.request.user,
        ).exclude(
            role__in=[ChatUserRole.BLOCKED.value, ChatUserRole.BLOCKER.value],
        ).values('chat_room_id')

        queryset = ChatMessage.objects.filter(chat_room_id__in=my_room_ids).select_related(
            'chat_room', 'created_by__profile', *attachment_related_names(),
        ).prefetch_related(
            'vote__options__ballots', 'payment_request__targets',
        # 채팅방 FK 인덱스 (chat_room, id) 를 그대로 타도록 id 로 정렬
        ).order_by('-id')
        room_id = self.request.query_params.get('chat_room')
        if room_id:
            queryset = queryset.filter(chat_room_id=room_id)
        return queryset

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
        # 배달 주문 / 도착 / 안내 메시지는 지우지 않는다 (주문은 주문 취소로)
        if instance.message_type not in DELETABLE_MESSAGE_TYPES:
            return response.Response(
                {"detail": "이 메시지는 삭제할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()  # 소프트 삭제가 아니라면 일반 delete()
        broadcast_room_update(instance.chat_room_id, "messages", "deleted", instance.id)
        return response.Response({"message": "메시지가 삭제되었습니다."}, status=status.HTTP_200_OK)