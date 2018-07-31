from rest_framework import serializers

from apps.core.models import Scrap


class BaseScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class ScrapSerializer(BaseScrapSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'

    from apps.core.serializers.article import BaseArticleSerializer
    parent_article = BaseArticleSerializer()


class ScrapCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
            'scrapped_by',
        )
