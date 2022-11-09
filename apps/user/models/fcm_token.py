from cached_property import cached_property
from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel


class FCMToken(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "FCM 토큰"
        verbose_name_plural = "FCM 푸시알림 토큰"

    user = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="fcm_token_set",
        verbose_name="유저",
    )

    token = models.CharField(
        max_length=200,
        primary_key=True,
        verbose_name="토큰",
    )

    last_activated_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="최근 토큰 부여 및 확인 시간",
    )
