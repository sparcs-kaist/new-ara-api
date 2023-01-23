from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Article, Notification

@receiver(models.signals.post_save, sender=Article)
def comment_post_save_signal(created, instance, **kwargs):
    if created:
        Notification.notify_article(instance)
