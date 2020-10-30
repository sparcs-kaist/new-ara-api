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
        for article_read_log in instance.article_read_log_set.all():
            article_read_log.deleted_at = instance.deleted_at
            article_read_log.save()

        for article_update_log in instance.article_update_log_set.all():
            article_update_log.deleted_at = instance.deleted_at
            article_update_log.save()

        for article_delete_log in instance.article_delete_log_set.all():
            article_delete_log.deleted_at = instance.deleted_at
            article_delete_log.save()

        for best in instance.best_set.all():
            best.deleted_at = instance.deleted_at
            best.save()

        for comment in instance.comment_set.all():
            comment.deleted_at = instance.deleted_at
            comment.save()

        for notification in instance.notification_set.all():
            notification.deleted_at = instance.deleted_at
            notification.save()

        for report in instance.report_set.all():
            report.deleted_at = instance.deleted_at
            report.save()

        for scrap in instance.scrap_set.all():
            scrap.deleted_at = instance.deleted_at
            scrap.save()

        for vote in instance.vote_set.all():
            vote.deleted_at = instance.deleted_at
            vote.save()


@receiver(models.signals.post_save, sender=Attachment)
def cascade_soft_deletion_attachment(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        for comment in instance.comment_set.all():
            comment.deleted_at = instance.deleted_at
            comment.save()


@receiver(models.signals.post_save, sender=Board)
def cascade_soft_deletion_board(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        for article in instance.article_set.all():
            article.deleted_at = instance.deleted_at
            article.save()

        for topic in instance.topic_set.all():
            topic.deleted_at = instance.deleted_at
            topic.save()


@receiver(models.signals.post_save, sender=Comment)
def cascade_soft_deletion_comment(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        for comment in instance.comment_set.all():
            comment.deleted_at = instance.deleted_at
            comment.save()

        for comment_update_log in instance.comment_update_log_set.all():
            comment_update_log.deleted_at = instance.deleted_at
            comment_update_log.save()

        for comment_delete_log in instance.comment_delete_log_set.all():
            comment_delete_log.deleted_at = instance.deleted_at
            comment_delete_log.save()

        for notification in instance.notification_set.all():
            notification.deleted_at = instance.deleted_at
            notification.save()

        for report in instance.report_set.all():
            report.deleted_at = instance.deleted_at
            report.save()

        for vote in instance.vote_set.all():
            vote.deleted_at = instance.deleted_at
            vote.save()


@receiver(models.signals.post_save, sender=Notification)
def cascade_soft_deletion_notification(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        for notification_read_log in instance.notification_read_log_set.all():
            notification_read_log.deleted_at = instance.deleted_at
            notification_read_log.save()


@receiver(models.signals.post_save, sender=Topic)
def cascade_soft_deletion_topic(instance, **kwargs):
    deleted = instance.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    if deleted:
        for article in instance.article_set.all():
            article.deleted_at = instance.deleted_at
            article.save()

