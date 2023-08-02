from apps.core.models import Topic
from ara.classes.serializers import MetaDataModelSerializer


class BaseTopicSerializer(MetaDataModelSerializer):
    class Meta:
        model = Topic
        fields = ["id", "slug", "ko_name", "en_name"]


class TopicSerializer(BaseTopicSerializer):
    pass


class BoardNestedTopicSerializer(BaseTopicSerializer):
    from apps.core.serializers.board import BoardSerializer

    board = BoardSerializer(
        read_only=True,
    )
