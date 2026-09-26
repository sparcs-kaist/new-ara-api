from rest_framework import (
    decorators,
    exceptions,
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from django.utils import timezone
from rest_framework.decorators import action
from django.db.models.functions import Greatest, Coalesce

from drf_spectacular.utils import extend_schema, extend_schema_view

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.room import ChatRoom, ChatRoomType, ChatNameType
from apps.chatting.models.membership_room import ChatRoomMemberShip, ChatUserRole
from apps.chatting.realtime import broadcast_member_removed, broadcast_room_update
from apps.chatting.serializers.room import  ChatRoomCreateSerializer, ChatRoomSerializer, ChatRoomDetailSerializer, ChatRoomUpdateSerializer
from apps.chatting.permissions.room import RoomReadPermission, RoomBlockPermission, RoomDeletePermission, RoomLeavePermission
from apps.user.serializers.user import PublicUserSerializer
from apps.chatting.serializers.message import MessageSerializer, attachment_related_names
from apps.chatting.serializers.member import prefill_member_directory
from ara.settings import MIN_TIME

# 방 정보 수정은 PATCH 만 (PUT 비활성화)
@extend_schema_view(
    update=extend_schema(exclude=True),
)

class ChatRoomViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = serializers.Serializer

    action_permission_classes = {
        "list": (permissions.IsAuthenticated,),
        "create": (permissions.IsAuthenticated,),
        "destroy": (RoomDeletePermission,),
        "leave": (permissions.IsAuthenticated, RoomLeavePermission),
        "read": (permissions.IsAuthenticated, RoomReadPermission),
        "block": (permissions.IsAuthenticated, RoomBlockPermission),
        "blocked": (permissions.IsAuthenticated,),
        "retrieve": (permissions.IsAuthenticated,),
        "partial_update": (permissions.IsAuthenticated,),
    }

    action_serializer_class = {
        "create": ChatRoomCreateSerializer,
        "list": ChatRoomSerializer,
        "blocked_list": ChatRoomSerializer,
        "partial_update": ChatRoomUpdateSerializer,
    }

    def update(self, request, *args, **kwargs):
        if not kwargs.get("partial"):
            raise exceptions.MethodNotAllowed("PUT")
        room = self.get_object()
        if ChatRoomMemberShip.get_active(room, request.user) is None:
            raise exceptions.PermissionDenied("채팅방 참여자가 아닙니다.")
        if room.room_type in [ChatRoomType.DM.value, ChatRoomType.DELIVERY.value]:
            raise exceptions.ValidationError({"detail": "이 채팅방은 이름과 사진을 바꿀 수 없습니다."})

        serializer = ChatRoomUpdateSerializer(room, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        broadcast_room_update(room.id, "room", "updated", room.id)
        return response.Response(ChatRoomSerializer(room, context={'request': request}).data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        rooms = page if page is not None else list(queryset)

        context = self.get_serializer_context()
        prefill_member_directory(context, [room.id for room in rooms])
        serializer = ChatRoomSerializer(rooms, many=True, context=context)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        room = self.get_object()
        if room.room_type == ChatRoomType.DELIVERY.value:
            return response.Response(
                {"detail": "함께 배달 방은 모집 취소로 닫아주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 부속 데이터 먼저 정리
        ChatRoomMemberShip.objects.filter(chat_room=room).delete() #User의 Membership 삭제
        room.room_permission.delete()  #Room에 설정된 Permission도 삭제 (1:1 관계이므로 바로 삭제)

        room.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        qs = ChatRoom.objects.select_related(
            'delivery_party',
            'recent_message__chat_room',
            'recent_message__created_by__profile',
            *[f'recent_message__{name}' for name in attachment_related_names()],
        ).prefetch_related(
            'recent_message__vote__options__ballots',
            'recent_message__payment_request__targets',
        )
        if self.request.method == "GET":
            qs = qs.filter(
                membership_info_set__user=self.request.user,
                membership_info_set__deleted_at=MIN_TIME,
            ).distinct()
            ordering = self.request.query_params.get('ordering')
            if not ordering:
                # 기본 정렬: created_at과 recent_message_at 중 더 최근인 값 기준
                qs = qs.annotate(
                    latest_at=Greatest(
                        'created_at',
                        Coalesce('recent_message_at', 'created_at'),
                    )
                ).order_by('-latest_at')
        return qs

    # chat/room/<roomid> (GET) : 해당 room의 자세한 정보 조회 (User정보 까지)
    @extend_schema(
        responses={200: ChatRoomDetailSerializer},
        description="특정 채팅방의 상세 정보(참여자, 최근 메시지 등) 반환"
    )
    def retrieve(self, request, *args, **kwargs):
        room = self.get_object()

        # 참여자 목록 가져오기
        memberships = ChatRoomMemberShip.objects.filter(chat_room=room).select_related('user__profile', 'chat_room')
        users = [membership.user for membership in memberships]

        # 본인이 참여한 채팅방이 아니면 403 반환
        if request.user not in users:
            return response.Response(
                {"detail": "이 채팅방 정보를 조회할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )

        room_data = ChatRoomSerializer(room, context={'request': request}).data
        
        # members 데이터를 membership 정보와 함께 구성
        # 익명 방에서는 유저 정보 대신 방 안의 이름(방장, 익명1 ...)만 내려준다
        is_anonymous = room.chat_name_type == ChatNameType.ANONYMOUS.value
        members_data = []
        for membership in memberships:
            members_data.append({
                'user': None if is_anonymous else PublicUserSerializer(membership.user).data,
                'display_name': membership.get_display_name(),
                'anon_number': membership.anon_number,
                'is_mine': membership.user_id == request.user.id,
                'role': membership.role,
                'last_seen_at': membership.last_seen_at
            })

        recent_message = room.message_set.order_by('-created_at').first()
        recent_message_data = MessageSerializer(recent_message, context={'request': request}).data if recent_message else None

        return response.Response({
            "room": room_data,
            "members": members_data,
            "recent_message": recent_message_data,
        })

    # chat/room/<roomid>/leave : 해당 room 나가기
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        room = self.get_object()
        # 주문 상태에 따라 나갈 수 있는지가 달라지므로 배달 API 에서 처리한다
        if room.room_type == ChatRoomType.DELIVERY.value:
            return response.Response(
                {"detail": "함께 배달 방은 배달 나가기 API 를 사용해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.delete()
            broadcast_member_removed(room.id, membership.anon_number)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    # chat/room/<roomid>/read : 해당 room의 채팅방 읽음 처리
    # @Todo : last_seen_message_id 도 업데이트 해야한다.
    @action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        room = self.get_object()
        membership = ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).first()
        if membership:
            membership.last_seen_at = timezone.now()
            
            # 최근 메시지 가져오기
            recent_message = room.message_set.order_by('-created_at').first()
            if recent_message:
                membership.last_seen_message = recent_message
            
            membership.save()
        return response.Response(status=status.HTTP_200_OK)

    # chat/room/<roomid>/block : 해당 room 차단.
    @action(detail=True, methods=["patch"])
    def block(self, request, pk=None):
        room = self.get_object()
        # 배달방 멤버십은 배달 API 에서만 바꾼다 (주문 / 정산 규칙 우회 방지)
        if room.room_type == ChatRoomType.DELIVERY.value:
            return response.Response(
                {"detail": "함께 배달 방은 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # 명시적으로 "unblock"이 true일 때만 차단 해제, 그 외에는 항상 차단
        unblock = request.data.get("unblock", False)

        # 참여하지 않은 방에 "차단 해제"로 들어가는 것 방지
        if unblock and not ChatRoomMemberShip.objects.filter(chat_room=room, user=request.user).exists():
            return response.Response(
                {"detail": "참여하거나 차단한 채팅방이 아닙니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
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
        if room.room_type == ChatRoomType.DELIVERY.value:
            return response.Response(
                {"detail": "함께 배달 방은 차단할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
