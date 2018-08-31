from rest_framework import serializers

from apps.core.models import Scrap


class BaseScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class ScrapSerializer(BaseScrapSerializer):
    from apps.core.serializers.article import ArticleListActionSerializer
    parent_article = ArticleListActionSerializer()

    from apps.session.serializers.user import PublicUserSerializer
    scrapped_by = PublicUserSerializer()


class ScrapCreateActionSerializer(serializers.ModelSerializer):
    class Meta(BaseScrapSerializer.Meta):
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
            'scrapped_by',
        )
