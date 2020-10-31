from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Article, Attachment, Board, Comment, Notification, Topic


# Core

@receiver(models.signals.post_save, sender=Article)
def cascade_soft_deletion_article(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.article_read_log_set.all().delete()
        instance.article_update_log_set.all().delete()
        instance.article_delete_log_set.all().delete()
        instance.best_set.all().delete()

        comments = instance.comment_set.all().delete()
        if comments:
            instance.update_comment_count()

        instance.notification_set.all().delete()
        instance.report_set.all().delete()
        instance.scrap_set.all().delete()
        instance.vote_set.all().delete()
        instance.attachments.all().delete()


@receiver(models.signals.post_save, sender=Board)
def cascade_soft_deletion_board(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.article_set.all().delete()
        instance.topic_set.all().delete()


@receiver(models.signals.post_save, sender=Comment)
def cascade_soft_deletion_comment(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        comments = instance.comment_set.all().delete()
        if comments:
            instance.parent_article.update_comment_count()

        instance.comment_update_log_set.all().delete()
        instance.comment_delete_log_set.all().delete()
        instance.notification_set.all().delete()
        instance.report_set.all().delete()
        instance.vote_set.all().delete()
        if instance.attachment:
            instance.attachment.delete()


@receiver(models.signals.post_save, sender=Notification)
def cascade_soft_deletion_notification(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.notification_read_log_set.all().delete()


@receiver(models.signals.post_save, sender=Topic)
def cascade_soft_deletion_topic(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.article_set.all().delete()
