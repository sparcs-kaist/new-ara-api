from rest_framework import serializers

from apps.core.models import CommentUpdateLog
from ara.classes.serializers import MetaDataModelSerializer


class BaseCommentUpdateLogSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommentUpdateLog
        fields = "__all__"


from rest_framework.utils.serializer_helpers import ReturnDict


class CommentUpdateLogSerializer(BaseCommentUpdateLogSerializer):
    data = serializers.JSONField(
        read_only=True,
    )  # type: ignore # 모르겠다 ..
