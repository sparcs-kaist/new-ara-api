import time

from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from apps.core.models import Report


@receiver(models.signals.post_save, sender=Report)
def report_post_save_signal(created, instance, **kwargs):
    #change threshold
    threshold = 5

    if created:
        #article report
        if (instance.parent_article != None):
            article = instance.parent_article
            article.update_report_count(article)
            if int(article.report_count % threshold) == 0:
                article.hidden_at = timezone.now()
                article.save()

        #comment report
        if (instance.parent_comment != None):
            comment = instance.parent_comment
            comment.update_report_count(comment)
            if int(comment.report_count % threshold) == 0:
                comment.hidden_at = timezone.now()
                comment.save()
