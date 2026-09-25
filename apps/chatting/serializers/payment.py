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
            'targets', 'total_amount', 'is_settled', 'canceled_at', 'created_at',
        ]

    def get_requester(self, obj):
        return member_summary(self, obj.message.chat_room, obj.message.created_by_id)

    def get_targets(self, obj):
        chat_room = obj.message.chat_room
        return [
            {
                "user": member_summary(self, chat_room, target.user_id),
                "amount": target.amount,
                "order_amount": target.order_amount,
                "delivery_fee_share": target.delivery_fee_share,
                "paid_at": target.paid_at,
            }
            for target in obj.targets.all()
        ]

    def get_total_amount(self, obj):
        return sum(target.amount for target in obj.targets.all())

    def get_is_settled(self, obj):
        return all(target.paid_at is not None for target in obj.targets.all())


# 익명 방에서는 유저 id 를 모르므로 anon_number 로도 대상을 지정할 수 있다 (둘 중 하나)
class ChatPaymentTargetInputSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    anon_number = serializers.IntegerField(min_value=0, required=False)
    amount = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        if ("user" in attrs) == ("anon_number" in attrs):
            raise serializers.ValidationError("user 와 anon_number 중 하나만 보내주세요.")
        return attrs


class ChatPaymentRequestCreateSerializer(serializers.Serializer):
    chat_room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
    bank_name = serializers.CharField(max_length=30)
    account_number = serializers.CharField(max_length=30)
    targets = ChatPaymentTargetInputSerializer(many=True, allow_empty=False)



class ChatPaymentPaidSerializer(serializers.Serializer):
    paid = serializers.BooleanField()
