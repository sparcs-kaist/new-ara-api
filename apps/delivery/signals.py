from django.db import models
from django.dispatch import receiver

from apps.chatting.models import ChatPaymentTarget


# 배달방 정산 대상자가 "송금 완료"를 누르면, 모두 보냈는지 보고 SETTLED 로 바꾼다
@receiver(models.signals.post_save, sender=ChatPaymentTarget)
def settle_delivery_party_when_paid(instance, **kwargs):
    if instance.paid_at is None:
        return

    from apps.delivery.models import DeliveryParty

    party = DeliveryParty.objects.filter(payment_request_id=instance.request_id).first()
    if party:
        party.settle_if_paid()
