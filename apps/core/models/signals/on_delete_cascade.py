from django.db import models, transaction
from django.dispatch import receiver

from ara.settings import MIN_TIME

from ..article import Article
from ..board import Board
from ..comment import Comment
from ..notification import Notification
from ..topic import Topic

# Core


@receiver(models.signals.post_save, sender=Article)
def cascade_soft_deletion_article(instance, **kwargs):
    deleted = instance.deleted_at != MIN_TIME

    if deleted:
        with transaction.atomic():
            instance.article_read_log_set.all().delete()
            instance.article_update_log_set.all().delete()
            instance.article_delete_log_set.all().delete()
            instance.best_set.all().delete()

            comments = instance.comment_set.filter(deleted_at=MIN_TIME).delete()
            if comments:
                instance.update_comment_count()

            instance.notification_set.all().delete()
            instance.report_set.all().delete()
            instance.scrap_set.all().delete()
            instance.vote_set.all().delete()
            instance.attachments.all().delete()


@receiver(models.signals.post_save, sender=Board)
def cascade_soft_deletion_board(instance, **kwargs):
    deleted = instance.deleted_at != MIN_TIME

    if deleted:
        with transaction.atomic():
            instance.article_set.all().delete()
            instance.topic_set.all().delete()


@receiver(models.signals.post_save, sender=Comment)
def cascade_soft_deletion_comment(instance, **kwargs):
    deleted = instance.deleted_at != MIN_TIME

    if deleted:
        with transaction.atomic():
            instance.comment_update_log_set.all().delete()
            instance.comment_delete_log_set.all().delete()
            instance.notification_set.all().delete()
            instance.report_set.all().delete()
            instance.vote_set.all().delete()

            if instance.attachment:
                instance.attachment.delete()


@receiver(models.signals.post_save, sender=Notification)
def cascade_soft_deletion_notification(instance, **kwargs):
    deleted = instance.deleted_at != MIN_TIME

    if deleted:
        instance.notification_read_log_set.all().delete()


@receiver(models.signals.post_save, sender=Topic)
def cascade_soft_deletion_topic(instance, **kwargs):
    deleted = instance.deleted_at != MIN_TIME

    if deleted:
        instance.article_set.all().delete()
