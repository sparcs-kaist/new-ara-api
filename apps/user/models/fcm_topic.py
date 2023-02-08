from django.conf import settings
from django.db import models
from django.utils import timezone


class FCMTopic(models.Model):
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="생성 시간",
    )

    user = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="fcm_topic_set",
        verbose_name="유저",
    )

    topic = models.CharField(max_length=200, verbose_name="알림 주제")

    class Meta:
        ordering = ("-created_at",)
        unique_together = (
            "user",
            "topic",
        )
