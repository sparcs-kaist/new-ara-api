from django.db import models

from django_mysql.models import JSONField

from ara.classes.model import MetaDataModel


TYPE_CHOICES = (
    ('default', 'default'),
)


def get_default_data():
    return {key: '' for key in ['title', 'body', 'icon', 'click_action']}


class Notification(MetaDataModel):
    class Meta:
        verbose_name = '알림'
        verbose_name_plural = '알림'

    data = JSONField(
        verbose_name='알림 JSON',
        default=get_default_data,
    )

    notification_type = models.CharField(
        verbose_name='알림 타입',
        choices=TYPE_CHOICES,
        max_length=256,
    )
