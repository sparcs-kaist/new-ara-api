from rest_framework import serializers


from apps.core.models import ArticleUpdateLog


class ArticleUpdateLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleUpdateLog
        fields = '__all__'

    from apps.core.serializers.topic import TopicSerializer
    from apps.core.serializers.board import BoardSerializer

    parent_topic = TopicSerializer()
    parent_board = BoardSerializer()

