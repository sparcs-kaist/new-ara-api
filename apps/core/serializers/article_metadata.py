from rest_framework import serializers

from apps.core.models import article_metadata
from ara.classes.serializers import MetaDataModelSerializer


class BaseArticleMetadataSerializer(MetaDataModelSerializer):
    class Meta:
        model = article_metadata.ArticleMetadata
        fields = "__all__"


class ArticleMetadataSerializer(BaseArticleMetadataSerializer):
    data = serializers.JSONField(
        read_only=True,
    )
