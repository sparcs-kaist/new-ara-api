from django.utils import timezone

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
        # 이미 스크랩이 존재할 경우 IntegrityError 를 띄우지 않고 생성 시간만 변경하도록 함
        scrap, _ = Scrap.objects.update_or_create(
            **validated_data,
            defaults={
                'created_at': timezone.now()
            }
        )
        return scrap
