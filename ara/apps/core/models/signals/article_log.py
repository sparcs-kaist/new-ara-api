from django.db import models
from django.dispatch import receiver

from apps.core.models import ArticleReadLog


@receiver(models.signals.post_save, sender=ArticleReadLog)
def article_read_log_post_save_signal(**kwargs):
    article_read_log = kwargs['instance']

    article_read_log.article.update_hit_count()
