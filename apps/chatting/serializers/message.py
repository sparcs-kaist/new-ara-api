from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from apps.chatting.models.message import ChatMessage
from apps.chatting.models.room import ChatRoom
from apps.user.serializers.user import PublicUserSerializer

class MessageSerializer(serializers.ModelSerializer):
    """
    메시지 조회용 시리얼라이저
    """
    created_by = PublicUserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        # message_id 제거 (실제 모델에서 제거됐다면)
        fields = [
            'id', 'message_type', 'message_content',
            'chat_room', 'created_by', 'created_at',
            'updated_at', 'expired_at'
        ]
        read_only_fields = [
            'id', 'created_by',
            'created_at', 'updated_at', 'expired_at'
        ]

class MessageCreateSerializer(serializers.ModelSerializer):
    """
    메시지 생성용 시리얼라이저
    """
    chat_room = serializers.PrimaryKeyRelatedField(
        queryset=ChatRoom.objects.all(),
        help_text="메시지를 보낼 채팅방 ID"
    )

    class Meta:
        model = ChatMessage
        fields = ['message_type', 'message_content', 'chat_room']

    def validate_message_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("메시지 내용이 비어있습니다.")
        return value

    def create(self, validated_data):
        validated_data['expired_at'] = timezone.now() + timedelta(days=30)
        return ChatMessage.create(**validated_data)

class MessageUpdateSerializer(serializers.ModelSerializer):
    """
    메시지 수정용 시리얼라이저
    """
    class Meta:
        model = ChatMessage
        fields = ['message_content']

    def validate_message_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("메시지 내용이 비어있습니다.")
        return value

class MessageDeleteResponseSerializer(serializers.Serializer):
    """
    메시지 삭제 응답용 시리얼라이저
    """
    message = serializers.CharField(help_text="삭제 결과 메시지")