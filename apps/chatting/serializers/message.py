from rest_framework import serializers
from apps.chatting.models.message import ChatMessage, ChatMessageType, USER_SENDABLE_MESSAGE_TYPES
from apps.chatting.models.room import ChatRoom
from apps.chatting.serializers.member import member_summary, is_anonymous_room
from apps.user.serializers.user import PublicUserSerializer

# {message_type: (related_name, serializer_class)}. 다른 앱은 register_message_attachment 로 등록한다
MESSAGE_ATTACHMENTS = {}

def register_message_attachment(message_type: str, related_name: str, serializer_class) -> None:
    MESSAGE_ATTACHMENTS[message_type] = (related_name, serializer_class)

def attachment_related_names() -> list[str]:
    return [related_name for related_name, _ in MESSAGE_ATTACHMENTS.values()]

class MessageSerializer(serializers.ModelSerializer):
    """
    메시지 조회용 시리얼라이저
    sender : 방 이름 표시 방식이 적용된 작성자 (SYSTEM 은 null)
    attachment : 타입별 데이터 (투표, 정산, 배달 주문)
    익명 방에서는 created_by 를 내려주지 않는다
    """
    created_by = PublicUserSerializer(read_only=True)
    sender = serializers.SerializerMethodField()
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            'id', 'message_type', 'message_content',
            'chat_room', 'created_by', 'sender', 'attachment',
            'created_at', 'updated_at', 'expired_at'
        ]
        read_only_fields = [
            'id', 'created_by',
            'created_at', 'updated_at', 'expired_at'
        ]

    def get_sender(self, obj):
        return member_summary(self, obj.chat_room, obj.created_by_id)

    def get_attachment(self, obj):
        if obj.message_type not in MESSAGE_ATTACHMENTS:
            return None
        related_name, serializer_class = MESSAGE_ATTACHMENTS[obj.message_type]
        related = getattr(obj, related_name, None)
        if related is None:
            return None
        return serializer_class(related, context=self.context).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if is_anonymous_room(instance.chat_room):
            data['created_by'] = None
        return data

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

    def validate_message_type(self, value):
        # 투표/정산/배달 메시지는 전용 API 로만 만든다
        if value not in USER_SENDABLE_MESSAGE_TYPES:
            raise serializers.ValidationError(f"{value} 메시지는 전용 API 로 보내야 합니다.")
        return value

    def validate_message_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("메시지 내용이 비어있습니다.")
        return value

    def create(self, validated_data):
        return ChatMessage.create(**validated_data)

class MessageUpdateSerializer(serializers.ModelSerializer):
    """
    메시지 수정용 시리얼라이저 (TEXT 메시지만 수정 가능)
    """
    class Meta:
        model = ChatMessage
        fields = ['message_content']

    def validate(self, attrs):
        if self.instance and self.instance.message_type != ChatMessageType.TEXT.value:
            raise serializers.ValidationError("텍스트 메시지만 수정할 수 있습니다.")
        return attrs

    def validate_message_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("메시지 내용이 비어있습니다.")
        return value

class MessageDeleteResponseSerializer(serializers.Serializer):
    """
    메시지 삭제 응답용 시리얼라이저
    """
    message = serializers.CharField(help_text="삭제 결과 메시지")


# 배달 타입은 apps.delivery 에서 등록
from apps.chatting.serializers.vote import ChatVoteSerializer
from apps.chatting.serializers.payment import ChatPaymentRequestSerializer

register_message_attachment(ChatMessageType.VOTE.value, "vote", ChatVoteSerializer)
register_message_attachment(ChatMessageType.PAYMENT_REQUEST.value, "payment_request", ChatPaymentRequestSerializer)
