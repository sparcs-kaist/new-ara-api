from rest_framework import serializers

from apps.core.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'

    from apps.core.serializers.topic import TopicSerializer
    from apps.core.serializers.board import BoardSerializer

    my_vote = serializers.SerializerMethodField()
    parent_topic = TopicSerializer()
    parent_board = BoardSerializer()

    def get_my_vote(self, obj):
        from apps.core.models import Vote

        try:
            return obj.vote_set.get(
                created_by=self.context['request'].user,
            ).is_positive

        except Vote.DoesNotExist:
            return None


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
        read_only_fields = (
            'id',
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
        read_only_fields = (
            'id',
        )
