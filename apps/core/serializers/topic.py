from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Topic


class BaseTopicSerializer(MetaDataModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"


class TopicSerializer(BaseTopicSerializer):
    pass


class BoardNestedTopicSerializer(BaseTopicSerializer):
    from apps.core.serializers.board import BoardSerializer

    board = BoardSerializer(
        read_only=True,
    )
