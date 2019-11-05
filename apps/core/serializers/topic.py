from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Topic
from apps.core.serializers.board import BoardSerializer


class BaseTopicSerializer(MetaDataModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'


class TopicSerializer(BaseTopicSerializer):
    pass


class BoardNestedTopicSerializer(BaseTopicSerializer):
    board = BoardSerializer(
        read_only=True,
    )
