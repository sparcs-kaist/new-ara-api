from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel

# 배달 주문 (DELIVERY_ORDER 메시지 하나에 주문 하나). 모인 금액 = 취소 안 된 price 합
class DeliveryOrder(MetaDataModel):
    message = models.OneToOneField(
        verbose_name = "주문 메시지",
        to = "chatting.ChatMessage",
        on_delete = models.CASCADE,
        related_name = "delivery_order",
    )
    party = models.ForeignKey(
        verbose_name = "배달방",
        to = "delivery.DeliveryParty",
        on_delete = models.CASCADE,
        related_name = "orders",
    )
    user = models.ForeignKey(
        verbose_name = "주문한 유저",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "delivery_orders",
    )
    # 배민 함께주문으로 메뉴를 담는 경우 비워둘 수 있다
    menu_name = models.CharField(
        verbose_name = "메뉴명",
        max_length = 100,
        blank = True,
        default = "",
    )
    price = models.PositiveIntegerField(
        verbose_name = "금액",
    )
    canceled_at = models.DateTimeField(
        verbose_name = "주문 취소 시각",
        null = True,
        blank = True,
        default = None,
    )

    @property
    def is_canceled(self) -> bool:
        return self.canceled_at is not None

    @property
    def summary(self) -> str:
        if self.menu_name:
            return f"{self.menu_name} · {self.price:,}원"
        return f"{self.price:,}원"
