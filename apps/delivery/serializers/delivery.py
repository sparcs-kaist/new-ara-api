from rest_framework import serializers

from apps.chatting.models import ChatRoomMemberShip
from apps.chatting.serializers.member import member_summary
from apps.delivery.models import DeliveryOrder, DeliveryParty, MAX_RECRUIT_MINUTES, MIN_RECRUIT_MINUTES


class DeliveryOrderSerializer(serializers.ModelSerializer):
    message_id = serializers.IntegerField(read_only=True)
    orderer = serializers.SerializerMethodField()
    is_canceled = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeliveryOrder
        fields = ['id', 'message_id', 'party', 'orderer', 'menu_name', 'price', 'is_canceled', 'created_at']

    def get_orderer(self, obj):
        return member_summary(self, obj.message.chat_room, obj.user_id)


class DeliveryPartyListSerializer(serializers.ModelSerializer):
    total_amount = serializers.IntegerField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = DeliveryParty
        fields = [
            'id', 'chat_room', 'store_name', 'place_name', 'place_detail',
            'min_order_amount', 'total_amount',
            'participant_count', 'max_participants',
            'deadline_at', 'status', 'created_at',
        ]


class DeliveryPartyDetailSerializer(DeliveryPartyListSerializer):
    host_orders = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    is_host = serializers.SerializerMethodField()
    payment_request = serializers.SerializerMethodField()
    can_request_payment = serializers.SerializerMethodField()

    class Meta(DeliveryPartyListSerializer.Meta):
        fields = DeliveryPartyListSerializer.Meta.fields + [
            'memo', 'order_link', 'recruit_minutes', 'decision_deadline_at', 'cancel_reason',
            'ordered_at', 'arrived_at', 'settled_at',
            'host_orders', 'members', 'orders', 'is_member', 'is_host', 'payment_request', 'can_request_payment',
        ]

    def get_viewer(self):
        request = self.context.get("request")
        return request.user if request else None

    def get_host_orders(self, obj):
        return [
            {"menu_name": order.menu_name, "price": order.price}
            for order in obj.active_orders().filter(user_id=obj.host_id)
        ]

    def get_members(self, obj):
        viewer = self.get_viewer()
        memberships = ChatRoomMemberShip.objects.filter(
            chat_room_id=obj.chat_room_id,
        ).select_related("chat_room").order_by("anon_number")
        return [
            {
                "display_name": m.get_display_name(),
                "anon_number": m.anon_number,
                "role": m.role,
                "is_mine": bool(viewer and viewer.id == m.user_id),
            }
            for m in memberships
        ]

    def get_orders(self, obj):
        if not self.get_is_member(obj):
            return None
        orders = obj.active_orders().select_related("message__chat_room")
        return DeliveryOrderSerializer(orders, many=True, context=self.context).data

    def get_payment_request(self, obj):
        request = obj.payment_request
        return request.id if request and request.is_active else None

    def get_can_request_payment(self, obj):
        return obj.can_request_payment

    def get_is_member(self, obj):
        viewer = self.get_viewer()
        return bool(viewer and obj.get_membership(viewer))

    def get_is_host(self, obj):
        viewer = self.get_viewer()
        return bool(viewer and viewer.id == obj.host_id)


class DeliveryPartyCreateSerializer(serializers.Serializer):
    store_name = serializers.CharField(max_length=100)
    place_name = serializers.CharField(max_length=100)
    place_detail = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    min_order_amount = serializers.IntegerField(min_value=0)
    recruit_minutes = serializers.IntegerField(min_value=MIN_RECRUIT_MINUTES, max_value=MAX_RECRUIT_MINUTES)
    max_participants = serializers.IntegerField(min_value=2, required=False, allow_null=True, default=None)
    memo = serializers.CharField(required=False, allow_blank=True, default="")
    order_link = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    # 방장 자신의 주문
    price = serializers.IntegerField(min_value=1)
    menu_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")


class DeliveryPartyUpdateSerializer(serializers.Serializer):
    memo = serializers.CharField(required=False, allow_blank=True)
    order_link = serializers.URLField(max_length=500, required=False, allow_blank=True)
    place_detail = serializers.CharField(max_length=100, required=False, allow_blank=True)
    max_participants = serializers.IntegerField(min_value=2, required=False, allow_null=True)


class DeliveryOrderUpdateSerializer(serializers.Serializer):
    price = serializers.IntegerField(min_value=1, required=False)
    menu_name = serializers.CharField(max_length=100, required=False, allow_blank=True)


class DeliveryKickSerializer(serializers.Serializer):
    anon_number = serializers.IntegerField(min_value=1)


class DeliveryOrderCreateSerializer(serializers.Serializer):
    price = serializers.IntegerField(min_value=1)
    menu_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")


class DeliveryExtendSerializer(serializers.Serializer):
    minutes = serializers.IntegerField(min_value=MIN_RECRUIT_MINUTES, max_value=MAX_RECRUIT_MINUTES)


class DeliveryPaymentRequestSerializer(serializers.Serializer):
    bank_name = serializers.CharField(max_length=30)
    account_number = serializers.CharField(max_length=30)
    delivery_fee = serializers.IntegerField(min_value=0, required=False, default=0)
