from django.db import models
from django.dispatch import receiver

from apps.chatting.models.message import ChatMessage
from apps.core.models import Notification

@receiver(models.signals.post_save, sender=ChatMessage)
def chat_message_post_save_signal(instance, created, **kwargs):
    if created:
        Notification.notify_message(instance)
