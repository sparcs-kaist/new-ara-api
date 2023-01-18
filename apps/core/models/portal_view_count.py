from django.db import models
from ara.db.models import MetaDataModel


class PortalViewCount(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "포탈 조회 기록"

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
