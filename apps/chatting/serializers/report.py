from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import exceptions, serializers

from apps.chatting.models import ChatMessage, ChatMessageType, ChatRoom, ChatRoomMemberShip
from apps.core.models.report import Report

User = get_user_model()

REPORT_COOLDOWN = timedelta(days=7)
CHAT_REPORT_KEYS = ("chat_message", "chat_room")


# 대상은 메시지 / 방 + 익명 번호 / 방 + 유저 id 중 하나
class ChatReportCreateSerializer(serializers.Serializer):
    chat_message = serializers.PrimaryKeyRelatedField(queryset=ChatMessage.objects.all(), required=False)
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all(), required=False)
    anon_number = serializers.IntegerField(min_value=0, required=False)
    reported_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    type = serializers.ChoiceField(choices=Report.TYPE_CHOICES)
    content = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if "chat_message" in attrs:
            if any(key in attrs for key in ("chat_room", "anon_number", "reported_user")):
                raise serializers.ValidationError("chat_message 를 보낼 때는 다른 대상을 함께 보내지 않아요.")
        elif "chat_room" not in attrs or ("anon_number" in attrs) == ("reported_user" in attrs):
            raise serializers.ValidationError(
                "chat_message 또는 chat_room + (anon_number 나 reported_user 중 하나) 가 필요해요."
            )
        return attrs


def create_chat_report(reporter, data) -> Report:
    message = data.get("chat_message")
    if message is not None:
        if message.message_type == ChatMessageType.SYSTEM.value or message.created_by_id is None:
            raise exceptions.ValidationError({"detail": "신고할 수 없는 메시지예요."})
        chat_room = message.chat_room
        reported_user_id = message.created_by_id
    else:
        chat_room = data["chat_room"]
        reported_user_id = data["reported_user"].id if "reported_user" in data else None

    if ChatRoomMemberShip.get_active(chat_room, reporter) is None:
        raise exceptions.PermissionDenied("채팅방 참여자가 아닙니다.")

    # 나간 멤버도 신고할 수 있도록 지난 멤버십까지 본다
    memberships = ChatRoomMemberShip.objects.queryset_with_deleted.filter(chat_room=chat_room).select_related("user")
    if reported_user_id is not None:
        target = memberships.filter(user_id=reported_user_id).order_by("-id").first()
    else:
        target = memberships.filter(anon_number=data["anon_number"]).order_by("-id").first()
    if target is None:
        raise exceptions.ValidationError({"detail": "방에 없는 사람이에요."})
    if target.user_id == reporter.id:
        raise exceptions.ValidationError({"detail": "자기 자신은 신고할 수 없어요."})
    if Report.objects.filter(
        reported_by=reporter,
        reported_user=target.user,
        chat_room=chat_room,
        created_at__gte=timezone.now() - REPORT_COOLDOWN,
    ).exists():
        raise exceptions.ValidationError({"detail": "이미 신고했어요."})

    return Report.objects.create(
        reported_by=reporter,
        reported_user=target.user,
        chat_room=chat_room,
        chat_message=message,
        type=data["type"],
        content=data["content"],
        reporter_email=reporter.email or "",
        reported_email=target.user.email or "",
    )
