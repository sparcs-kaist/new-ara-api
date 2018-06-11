from rest_framework import serializers


from apps.core.models import ArticleUpdateLog


class ArticleUpdateLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleUpdateLog
        fields = '__all__'

    data = serializers.JSONField()
