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
