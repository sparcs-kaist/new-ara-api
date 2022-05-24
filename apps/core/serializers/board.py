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
    user_readable = serializers.SerializerMethodField()
    user_writable = serializers.SerializerMethodField()

    def get_user_readable(self, obj):
        user = self.context['request'].user
        return obj.group_has_read_access(user.profile.group)

    def get_user_writable(self, obj):
        user = self.context['request'].user
        return obj.group_has_write_access(user.profile.group)
