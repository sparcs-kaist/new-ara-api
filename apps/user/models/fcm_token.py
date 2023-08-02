from django.conf import settings
from django.db import models
from django.utils import timezone


class FCMToken(models.Model):
    class Meta:
        ordering = ("-created_at",)

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="생성 시간",
    )

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

    is_web = models.BooleanField(
        default=True, db_index=True, verbose_name="토큰 부여 플랫폼이 웹인지 여부"
    )
