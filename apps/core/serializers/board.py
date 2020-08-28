from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Board


class BaseBoardSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = '__all__'


class BoardSerializer(BaseBoardSerializer):
    pass


class BoardDetailActionSerializer(BaseBoardSerializer):
    from apps.core.serializers.topic import TopicSerializer
    topics = TopicSerializer(
        many=True,
        read_only=True,
        source='topic_set',
    )
