from rest_framework import serializers

from apps.core.models.board import Board
from ara.classes.serializers import MetaDataModelSerializer


class BaseBoardSerializer(MetaDataModelSerializer):
    class Meta:
        model = Board
        fields = [
            "id",
            "slug",
            "ko_name",
            "en_name",
            "is_readonly",
            "name_type",
            "group",
            "banner_image",
            "ko_banner_description",
            "en_banner_description",
            "top_threshold",
        ]
        depth = 1


class SimpleBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ["id", "slug", "ko_name", "en_name"]


class BoardSerializer(BaseBoardSerializer):
    pass


class BoardDetailActionSerializer(BaseBoardSerializer):
    from apps.core.serializers.topic import TopicSerializer

    topics = TopicSerializer(
        many=True,
        read_only=True,
        source="topic_set",
    )
    user_readable = serializers.SerializerMethodField()
    user_writable = serializers.SerializerMethodField()

    class Meta(BaseBoardSerializer.Meta):
        fields = BaseBoardSerializer.Meta.fields + [
            "topics",
            "user_readable",
            "user_writable",
        ]

    def get_user_readable(self, obj: Board):
        return obj.permission_list_by_user(self.context["request"].user).READ

    def get_user_writable(self, obj: Board):
        return obj.permission_list_by_user(self.context["request"].user).WRITE
