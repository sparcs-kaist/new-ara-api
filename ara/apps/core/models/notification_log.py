from django.db import models

from ara.db.models import MetaDataModel


class NotificationReadLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '알림 조회 기록'
        verbose_name_plural = '알림 조회 기록 목록'
        unique_together = (
            ('read_by', 'notification', 'deleted_at'),
        )

    is_read = models.BooleanField(
        default=False,
        verbose_name='조회 여부',
    )

    read_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='notification_read_log_set',
        verbose_name='관련 사용자',
    )
    notification = models.ForeignKey(
        to='core.Notification',
        db_index=True,
        related_name='notification_read_log_set',
        verbose_name='관련 알림',
    )
