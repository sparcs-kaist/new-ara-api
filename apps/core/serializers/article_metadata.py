from rest_framework import serializers

from apps.core.models import article_metadata
from ara.classes.serializers import MetaDataModelSerializer


class ArticleMetadataSerializer(MetaDataModelSerializer):
    class Meta:
        model = article_metadata.ArticleMetadata
        fields = ("metadata",)  # JSON 필드만 노출
