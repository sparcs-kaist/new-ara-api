from django.db import models

from ara.db.models import MetaDataModel


class PortalViewCount(MetaDataModel):
    article = models.ForeignKey(
        to="core.Article",
        on_delete=models.CASCADE,
        related_name="게시물",
        null=False,
    )

    view_count = models.PositiveIntegerField(
        verbose_name="조회수",
        default=0,
    )
