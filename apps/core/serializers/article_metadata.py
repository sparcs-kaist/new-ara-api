from rest_framework import serializers

from apps.core.models import article_metadata


class BaseArticleMetadataSerializer(MetaDataModelSerializer):
    class Meta:
        model = article_metadata.ArticleMetadata
        fields = "__all__"


class ArticleMetadataSerializer(BaseArticleMetadataSerializer):
    data = serializers.JSONField(
        read_only=True,
    )
