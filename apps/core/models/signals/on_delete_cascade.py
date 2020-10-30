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
        instance.article_read_log_set.all().update(deleted_at=instance.deleted_at)
        instance.article_update_log_set.all().update(deleted_at=instance.deleted_at)
        instance.article_delete_log_set.all().update(deleted_at=instance.deleted_at)
        instance.best_set.all().update(deleted_at=instance.deleted_at)
        instance.comment_set.all().update(deleted_at=instance.deleted_at)
        instance.notification_set.all().update(deleted_at=instance.deleted_at)
        instance.report_set.all().update(deleted_at=instance.deleted_at)
        instance.scrap_set.all().update(deleted_at=instance.deleted_at)
        instance.vote_set.all().update(deleted_at=instance.deleted_at)


@receiver(models.signals.post_save, sender=Attachment)
def cascade_soft_deletion_attachment(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.comment_set.all().update(deleted_at=instance.deleted_at)


@receiver(models.signals.post_save, sender=Board)
def cascade_soft_deletion_board(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.article_set.all().update(deleted_at=instance.deleted_at)
        instance.topic_set.all().update(deleted_at=instance.deleted_at)


@receiver(models.signals.post_save, sender=Comment)
def cascade_soft_deletion_comment(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.comment_set.all().update(deleted_at=instance.deleted_at)
        instance.comment_update_log_set.all().update(deleted_at=instance.deleted_at)
        instance.comment_delete_log_set.all().update(deleted_at=instance.deleted_at)
        instance.notification_set.all().update(deleted_at=instance.deleted_at)
        instance.report_set.all().update(deleted_at=instance.deleted_at)
        instance.vote_set.all().update(deleted_at=instance.deleted_at)


@receiver(models.signals.post_save, sender=Notification)
def cascade_soft_deletion_notification(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.notification_read_log_set.all().update(deleted_at=instance.deleted_at)


@receiver(models.signals.post_save, sender=Topic)
def cascade_soft_deletion_topic(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        instance.article_set.all().update(deleted_at=instance.deleted_at)
