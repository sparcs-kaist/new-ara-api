from rest_framework import serializers

from apps.core.models import Scrap
from apps.core.serializers.article import BaseArticleSerializer


class ScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'

    parent_article = BaseArticleSerializer()


class ScrapCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'
        read_only_fields = (
            'scrapped_by',
        )
