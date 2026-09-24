from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    name = "apps.delivery"
    label = "delivery"
    verbose_name = "함께 배달"

    def ready(self):
        from apps.chatting.models import ChatMessageType
        from apps.chatting.serializers.message import register_message_attachment
        from apps.delivery.serializers.delivery import DeliveryOrderSerializer
        from apps.delivery import signals  # noqa: F401

        # DELIVERY_ORDER 메시지에 주문 정보를 붙여서 내려준다
        register_message_attachment(
            ChatMessageType.DELIVERY_ORDER.value, "delivery_order", DeliveryOrderSerializer,
        )
