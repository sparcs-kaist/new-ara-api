from rest_framework import serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import CommentUpdateLog


class CommentUpdateLogSerializer(MetaDataModelSerializer):
    class Meta:
        model = CommentUpdateLog
        fields = '__all__'

    data = serializers.JSONField()
