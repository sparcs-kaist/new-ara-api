from rest_framework import serializers

from apps.core.models import Topic


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )


class BoardNestedTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
        read_only_fields = (
            'created_at',
            'updated_at',
            'deleted_at',
        )

    from apps.core.serializers.board import BoardSerializer

    board = BoardSerializer()
