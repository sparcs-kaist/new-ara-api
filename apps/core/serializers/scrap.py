from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Scrap
from apps.core.serializers.article import ArticleListActionSerializer
from apps.user.serializers.user import PublicUserSerializer


class BaseScrapSerializer(MetaDataModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'


class ScrapSerializer(BaseScrapSerializer):
    parent_article = ArticleListActionSerializer(
        read_only=True,
    )

    scrapped_by = PublicUserSerializer(
        read_only=True,
    )


class ScrapCreateActionSerializer(MetaDataModelSerializer):
    class Meta(BaseScrapSerializer.Meta):
        read_only_fields = (
            'scrapped_by',
        )
