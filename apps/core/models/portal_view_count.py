from django.db import models
from ara.db.models import MetaDataModel
from django.utils import timezone

class PortalViewCount(MetaDataModel):
    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Article",
        null=False,
        related_name="게시물",
    )

    view_count = models.IntegerField(
        default=0,
        verbose_name="조회수 값",
    )


    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name="생성 시간",
    )
