from rest_framework import serializers

from apps.core.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )

    from apps.core.serializers.topic import TopicSerializer
    from apps.core.serializers.board import BoardSerializer

    parent_topic = TopicSerializer()
    parent_board = BoardSerializer()


class ArticleCreateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = (
            'title',
            'content',
            'is_anonymous',
            'is_content_sexual',
            'is_content_social',
            'use_signature',
            'parent_topic',
            'parent_board',
        )


class ArticleUpdateActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = (
            'title',
            'content',
            'is_content_sexual',
            'is_content_social',
        )
