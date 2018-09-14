from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import ArticleUpdateLog


class ArticleUpdateLogSerializer(MetaDataModelSerializer):
    class Meta:
        model = ArticleUpdateLog
        fields = '__all__'

    data = serializers.JSONField()
