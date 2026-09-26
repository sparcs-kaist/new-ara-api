from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel

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

    @staticmethod
    def make_summary(menu_name: str, price: int) -> str:
        return f"{menu_name} · {price:,}원" if menu_name else f"{price:,}원"

    @property
    def summary(self) -> str:
        return self.make_summary(self.menu_name, self.price)
