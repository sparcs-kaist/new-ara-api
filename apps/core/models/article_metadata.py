from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel

#거래 게시판의 가격 등과 같은 정보를 기록하기 위한
class ArticleMetadata(MetaDataModel):

    article = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Article",
        related_name="article_metadata_set",
        verbose_name="메타데이터를 갖는 게시글",
        db_index = True,
    )

    metadata = models.JSONField(
        verbose_name = "게시글 메타데이터",
        default = dict,
        blank = True,
        null = True,
    )