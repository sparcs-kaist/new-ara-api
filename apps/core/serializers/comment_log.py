from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import CommentUpdateLog


class BaseCommentUpdateLogSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommentUpdateLog
        fields = '__all__'


class CommentUpdateLogSerializer(BaseCommentUpdateLogSerializer):
    data = serializers.JSONField(
        read_only=True,
    )
