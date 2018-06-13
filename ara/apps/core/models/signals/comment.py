import datetime

from django.db import models
from django.dispatch import receiver

from apps.core.models import Comment, Notification


@receiver(models.signals.post_save, sender=Comment)
def comment_post_save_signal(**kwargs):
    def notify_commented(comment):
        Notification.notify_commented(comment)

    def update_article_commented_at(comment):
        if comment.parent_article:
            comment.parent_article.commented_at = datetime.datetime.now()
            comment.parent_article.save()

        else:
            comment.parent_comment.parent_article.commented_at = datetime.datetime.now()
            comment.parent_comment.parent_article.save()

    comment = kwargs['instance']

    if kwargs['created']:
        notify_commented(comment)
        update_article_commented_at(comment)
