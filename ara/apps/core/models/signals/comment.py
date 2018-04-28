from django.db import models
from django.dispatch import receiver

from apps.core.models import Comment, Notification


@receiver(models.signals.post_save, sender=Comment)
def comment_post_save_signal(**kwargs):
    def notify_commented(comment):
        Notification.notify_commented(comment)

    if kwargs['created']:
        notify_commented(kwargs['instance'])
