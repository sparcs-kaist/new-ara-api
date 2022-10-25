from django.db import models
from django.conf import settings

from ara.db.models import MetaDataModel


class NotificationReadLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "알림 조회 기록"
        verbose_name_plural = "알림 조회 기록 목록"
        unique_together = (("read_by", "notification", "deleted_at"),)

    is_read = models.BooleanField(
        default=False,
        verbose_name="조회 여부",
    )

    read_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name="notification_read_log_set",
        verbose_name="관련 사용자",
    )
    notification = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Notification",
        db_index=True,
        related_name="notification_read_log_set",
        verbose_name="관련 알림",
    )

    @classmethod
    def prefetch_my_notification_read_log(cls, user, prefix="") -> models.Prefetch:
        return models.Prefetch(
            "{}notification_read_log_set".format(prefix),
            queryset=NotificationReadLog.objects.filter(
                read_by=user,
            ),
        )
