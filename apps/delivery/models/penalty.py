from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from ara.db.models import MetaDataModel

# 처음엔 3시간, 최근 30일 안에 또 받으면 하루
FIRST_PENALTY = timedelta(hours=3)
REPEAT_PENALTY = timedelta(days=1)
REPEAT_WINDOW = timedelta(days=30)

# 방장이 다른 사람 주문을 두고 모집을 깼을 때. 기간 동안 방 개설만 막는다
class DeliveryPenalty(MetaDataModel):
    user = models.ForeignKey(
        verbose_name = "패널티 받은 유저",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "delivery_penalties",
    )
    party = models.ForeignKey(
        verbose_name = "패널티 원인 배달방",
        to = "delivery.DeliveryParty",
        on_delete = models.CASCADE,
        related_name = "penalties",
    )
    until = models.DateTimeField(
        verbose_name = "방 개설 금지 해제 시각",
    )

    @classmethod
    def give(cls, user_id, party) -> "DeliveryPenalty":
        now = timezone.now()
        is_repeat = cls.objects.filter(user_id=user_id, created_at__gte=now - REPEAT_WINDOW).exists()
        duration = REPEAT_PENALTY if is_repeat else FIRST_PENALTY
        return cls.objects.create(user_id=user_id, party=party, until=now + duration)

    # 지금 패널티 중이면 해제 시각, 아니면 None
    @classmethod
    def active_until(cls, user):
        return cls.objects.filter(
            user=user,
            until__gt=timezone.now(),
        ).order_by("-until").values_list("until", flat=True).first()
