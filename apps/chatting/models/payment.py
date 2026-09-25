from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from ara.db.models import MetaDataModel
from apps.chatting.models.message import ChatMessage, ChatMessageType

# 송금(정산) 요청 (PAYMENT_REQUEST 메시지 하나에 요청 하나)
# 대상자마다 금액이 다를 수 있고, 각자 "송금 완료"를 누른다
class ChatPaymentRequest(MetaDataModel):
    message = models.OneToOneField(
        verbose_name = "정산 요청 메시지",
        to = "chatting.ChatMessage",
        on_delete = models.CASCADE,
        related_name = "payment_request",
    )
    bank_name = models.CharField(
        verbose_name = "은행",
        max_length = 30,
    )
    # 앞자리 0, 하이픈 때문에 문자열
    account_number = models.CharField(
        verbose_name = "계좌번호",
        max_length = 30,
    )

    def lock_row(self):
        list(ChatPaymentRequest.objects.select_for_update().filter(pk=self.pk).values_list("pk", flat=True))

    def has_paid_target(self) -> bool:
        return self.targets.filter(paid_at__isnull=False).exists()

    @property
    def is_settled(self) -> bool:
        return not self.targets.filter(paid_at__isnull=True).exists()

    # targets : [(user, amount), ...]
    @classmethod
    @transaction.atomic
    def create_with_message(cls, chat_room, created_by, bank_name: str, account_number: str, targets):
        total = sum(amount for _, amount in targets)
        message = ChatMessage.create(
            chat_room=chat_room,
            created_by=created_by,
            message_type=ChatMessageType.PAYMENT_REQUEST.value,
            # 계좌번호는 미리보기 / 푸시에 넣지 않는다
            message_content=f"[정산 요청] 총 {total:,}원",
        )
        payment_request = cls.objects.create(
            message=message,
            bank_name=bank_name,
            account_number=account_number,
        )
        ChatPaymentTarget.objects.bulk_create([
            ChatPaymentTarget(request=payment_request, user=user, amount=amount)
            for user, amount in targets
        ])
        return payment_request


class ChatPaymentTarget(MetaDataModel):
    request = models.ForeignKey(
        verbose_name = "정산 요청",
        to = ChatPaymentRequest,
        on_delete = models.CASCADE,
        related_name = "targets",
    )
    user = models.ForeignKey(
        verbose_name = "송금할 유저",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "chat_payment_targets",
    )
    amount = models.PositiveIntegerField(
        verbose_name = "송금할 금액",
    )
    paid_at = models.DateTimeField(
        verbose_name = "송금 완료 시각",
        null = True,
        blank = True,
        default = None,
    )

    class Meta(MetaDataModel.Meta):
        unique_together = (("request", "user", "deleted_at"),)

    def set_paid(self, paid: bool) -> None:
        self.paid_at = timezone.now() if paid else None
        self.save()
