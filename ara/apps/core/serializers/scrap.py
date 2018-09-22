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
