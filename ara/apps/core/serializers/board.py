from rest_framework import serializers

from apps.core.models import Board


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )


class BoardDetailActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )

    from apps.core.serializers.topic import TopicSerializer

    topics = TopicSerializer(
        many=True,
        source='topic_set',
    )


class BoardRecentArticleActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )

    recent_articles = serializers.SerializerMethodField()

    def get_recent_articles(self, obj):
        from apps.core.serializers.article import ArticleSerializer

        return ArticleSerializer(
            instance=obj.article_set.order_by('-id')[:5],
            many=True,
            **{'context': {'request': self.context.get('request')}}
        ).data
