from django.db import IntegrityError
from django.utils.translation import gettext
from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer
from apps.core.models import Scrap


class BaseScrapSerializer(MetaDataModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class ScrapSerializer(BaseScrapSerializer):
    from apps.core.serializers.article import ArticleListActionSerializer
    parent_article = ArticleListActionSerializer(
        read_only=True,
    )

    from apps.user.serializers.user import PublicUserSerializer
    scrapped_by = PublicUserSerializer(
        read_only=True,
    )


class ScrapCreateActionSerializer(MetaDataModelSerializer):
    class Meta(BaseScrapSerializer.Meta):
        read_only_fields = (
            'scrapped_by',
        )

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(gettext("This article is already scrapped."))
