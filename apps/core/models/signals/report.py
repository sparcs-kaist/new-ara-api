from django.db import models
from django.dispatch import receiver

from apps.core.models import Report


@receiver(models.signals.post_save, sender=Report)
def report_post_save_signal(created, instance, **kwargs):
    # change REPORT_THRESHOLD at ara/settings/dev/__init__.py or ara/settings/prod/__init__.py
    if created:
        # article report
        if instance.parent_article != None:
            article = instance.parent_article
            article.update_report_count()
        # comment report
        if instance.parent_comment != None:
            comment = instance.parent_comment
            comment.update_report_count()
