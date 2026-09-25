from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, permissions, response, status

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models import ChatMessageType, ChatReport, ChatRoomMemberShip
from apps.chatting.serializers.report import ChatReportCreateSerializer
from apps.chatting.views.viewsets.vote import get_membership_or_403


class ChatReportViewSet(ActionAPIViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ChatReportCreateSerializer

    # 응답에는 신고 id 만 준다. 피신고자에게 알림은 가지 않는다
    @extend_schema(request=ChatReportCreateSerializer, responses={201: None})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        message = data.get("message")
        if message is not None:
            if message.message_type == ChatMessageType.SYSTEM.value or message.created_by_id is None:
                raise exceptions.ValidationError({"detail": "신고할 수 없는 메시지예요."})
            chat_room = message.chat_room
            reported_user_id = message.created_by_id
        else:
            chat_room = data["chat_room"]
            reported_user_id = data["reported_user"].id if "reported_user" in data else None

        get_membership_or_403(chat_room, request.user)

        # 나간 멤버도 신고할 수 있도록 지난 멤버십까지 본다
        memberships = ChatRoomMemberShip.objects.queryset_with_deleted.filter(chat_room=chat_room)
        if reported_user_id is not None:
            target = memberships.filter(user_id=reported_user_id).select_related("user").order_by("-id").first()
        else:
            target = memberships.filter(anon_number=data["anon_number"]).select_related("user").order_by("-id").first()
        if target is None:
            raise exceptions.ValidationError({"detail": "방에 없는 사람이에요."})
        if target.user_id == request.user.id:
            raise exceptions.ValidationError({"detail": "자기 자신은 신고할 수 없어요."})
        if ChatReport.reported_recently(request.user, target.user, chat_room):
            raise exceptions.ValidationError({"detail": "이미 신고했어요."})

        report = ChatReport.objects.create(
            reported_by=request.user,
            reported_user=target.user,
            chat_room=chat_room,
            message=message,
            reported_anon_number=target.anon_number,
            type=data["type"],
            content=data["content"],
            reporter_email=request.user.email or "",
            reported_email=target.user.email or "",
        )
        return response.Response({"id": report.id}, status=status.HTTP_201_CREATED)
