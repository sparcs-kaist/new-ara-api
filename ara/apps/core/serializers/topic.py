from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Topic


class TopicSerializer(MetaDataModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'


class BoardNestedTopicSerializer(MetaDataModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'

    from apps.core.serializers.board import BoardSerializer

    board = BoardSerializer()
