from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Board


class BoardSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'


class BoardDetailActionSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'

    from apps.core.serializers.topic import TopicSerializer

    topics = TopicSerializer(
        many=True,
        source='topic_set',
    )


class BoardRecentArticleActionSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'

    recent_articles = serializers.SerializerMethodField()

    def get_recent_articles(self, obj):
        from apps.core.serializers.article import ArticleListActionSerializer

        return ArticleListActionSerializer(
            instance=obj.article_set.all()[:5],
            many=True,
            **{'context': {'request': self.context.get('request')}}
        ).data
