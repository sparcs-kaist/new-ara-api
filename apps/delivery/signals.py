from django.db import models
from django.dispatch import receiver

from apps.chatting.models import ChatMessage, ChatMessageType, ChatPaymentRequest, ChatPaymentTarget


def settle_party_in_room(chat_room_id):
    from apps.delivery.models import DeliveryParty

    party = DeliveryParty.objects.filter(chat_room_id=chat_room_id).first()
    if party:
        party.settle_if_paid()


@receiver(models.signals.post_save, sender=ChatPaymentTarget)
def settle_when_paid(instance, **kwargs):
    if instance.paid_at is not None:
        settle_party_in_room(instance.request.message.chat_room_id)


@receiver(models.signals.post_save, sender=ChatPaymentRequest)
def settle_when_canceled(instance, created, **kwargs):
    if not created and instance.canceled_at is not None:
        settle_party_in_room(instance.message.chat_room_id)


@receiver(models.signals.post_save, sender=ChatMessage)
def settle_when_payment_deleted(instance, created, **kwargs):
    if not created and instance.message_type == ChatMessageType.PAYMENT_REQUEST.value:
        settle_party_in_room(instance.chat_room_id)
