from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Board
from apps.core.serializers.article import ArticleListActionSerializer
from apps.core.serializers.topic import TopicSerializer


class BaseBoardSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'

    def get_recent_articles(self, obj):
        return ArticleListActionSerializer(
            instance=obj.article_set.all()[:5],
            many=True,
            **{'context': {'request': self.context.get('request')}}
        ).data


class BoardSerializer(BaseBoardSerializer):
    pass


class BoardDetailActionSerializer(BaseBoardSerializer):
    topics = TopicSerializer(
        many=True,
        read_only=True,
        source='topic_set',
    )


class BoardRecentArticleActionSerializer(BaseBoardSerializer):
    recent_articles = serializers.SerializerMethodField(
        read_only=True,
    )
