from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import ArticleUpdateLog


class BaseArticleUpdateLogSerializer(MetaDataModelSerializer):
    class Meta:
        model = ArticleUpdateLog
        fields = "__all__"


class ArticleUpdateLogSerializer(BaseArticleUpdateLogSerializer):
    data = serializers.JSONField(
        read_only=True,
    )
