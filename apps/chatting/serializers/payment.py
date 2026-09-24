from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.chatting.models.payment import ChatPaymentRequest
from apps.chatting.models.room import ChatRoom
from apps.chatting.serializers.member import member_summary

User = get_user_model()


class ChatPaymentRequestSerializer(serializers.ModelSerializer):
    """정산 요청 조회용 (메시지 attachment 로도 쓰임)"""
    message_id = serializers.IntegerField(read_only=True)
    chat_room = serializers.IntegerField(source="message.chat_room_id", read_only=True)
    requester = serializers.SerializerMethodField()
    targets = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    is_settled = serializers.SerializerMethodField()

    class Meta:
        model = ChatPaymentRequest
        fields = [
            'id', 'message_id', 'chat_room', 'requester', 'bank_name', 'account_number',
            'targets', 'total_amount', 'is_settled', 'created_at',
        ]

    def get_requester(self, obj):
        return member_summary(self, obj.message.chat_room, obj.message.created_by_id)

    def get_targets(self, obj):
        chat_room = obj.message.chat_room
        return [
            {
                "user": member_summary(self, chat_room, target.user_id),
                "amount": target.amount,
                "paid_at": target.paid_at,
            }
            for target in obj.targets.all()
        ]

    def get_total_amount(self, obj):
        return sum(target.amount for target in obj.targets.all())

    def get_is_settled(self, obj):
        return all(target.paid_at is not None for target in obj.targets.all())


class ChatPaymentTargetInputSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    amount = serializers.IntegerField(min_value=1)


class ChatPaymentRequestCreateSerializer(serializers.Serializer):
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    bank_name = serializers.CharField(max_length=30)
    account_number = serializers.CharField(max_length=30)
    targets = ChatPaymentTargetInputSerializer(many=True, allow_empty=False)

    def validate_targets(self, value):
        user_ids = [target["user"].id for target in value]
        if len(set(user_ids)) != len(user_ids):
            raise serializers.ValidationError("같은 대상자가 두 번 들어있습니다.")
        return value


class ChatPaymentPaidSerializer(serializers.Serializer):
    paid = serializers.BooleanField()
