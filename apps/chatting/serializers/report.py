from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.chatting.models import ChatMessage, ChatRoom
from apps.core.models.report import Report

User = get_user_model()


# 대상은 셋 중 하나: 메시지 / 방 + 익명 번호 (익명 방) / 방 + 유저 id (일반 방)
class ChatReportCreateSerializer(serializers.Serializer):
    message = serializers.PrimaryKeyRelatedField(queryset=ChatMessage.objects.all(), required=False)
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all(), required=False)
    anon_number = serializers.IntegerField(min_value=0, required=False)
    reported_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    type = serializers.ChoiceField(choices=Report.TYPE_CHOICES)
    content = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if "message" in attrs:
            if any(key in attrs for key in ("chat_room", "anon_number", "reported_user")):
                raise serializers.ValidationError("message 를 보낼 때는 다른 대상을 함께 보내지 않아요.")
        elif "chat_room" not in attrs or ("anon_number" in attrs) == ("reported_user" in attrs):
            raise serializers.ValidationError("message 또는 chat_room + (anon_number 나 reported_user 중 하나) 가 필요해요.")
        return attrs
