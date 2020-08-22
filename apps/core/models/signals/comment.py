from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Comment, Notification


@receiver(models.signals.post_save, sender=Comment)
def comment_post_save_signal(**kwargs):
    def notify_commented(comment):
        Notification.notify_commented(comment)

    def update_article_commented_at(comment):
        article = comment.parent_article if comment.parent_article else comment.parent_comment.parent_article
        article.commented_at = timezone.now()
        article.save()

    comment = kwargs['instance']

    if kwargs['created']:
        notify_commented(comment)
        update_article_commented_at(comment)
