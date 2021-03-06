from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Comment, Notification


@receiver(models.signals.post_save, sender=Comment)
def comment_post_save_signal(created, instance, **kwargs):
    def notify_commented(comment):
        Notification.notify_commented(comment)

    def update_article_comment_count(comment):
        parent_article = comment.get_parent_article()

        parent_article.update_comment_count()

    def update_article_commented_at(comment):
        article = comment.parent_article if comment.parent_article else comment.parent_comment.parent_article
        article.commented_at = timezone.now()
        article.save()

    if created:
        notify_commented(instance)
        update_article_comment_count(instance)
        update_article_commented_at(instance)

    else:
        # in case of MetaDataModel's instance deleted
        if instance.deleted_at != timezone.datetime.min:
            update_article_comment_count(instance)
