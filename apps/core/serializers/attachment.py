from pathlib import PurePath

from django.conf import settings
from rest_framework import serializers

from apps.core.models.attachment import Attachment, attachment_extension_validator
from ara.classes.serializers import MetaDataModelSerializer

S3_PUT_MAX_BYTES = 5 * 1024**3


class BaseAttachmentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"


class AttachmentSerializer(BaseAttachmentSerializer):
    pass


class StartAttachmentUploadSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    alias = serializers.CharField(max_length=255, required=False, allow_blank=True)
    size = serializers.IntegerField(min_value=1, max_value=S3_PUT_MAX_BYTES)

    def validate_filename(self, value: str) -> str:
        if "/" in value or "\\" in value:
            raise serializers.ValidationError("Provide a filename without a path.")
        attachment_extension_validator(PurePath(value))
        return value

    def validate_size(self, value: int) -> int:
        if value > settings.ATTACHMENT_UPLOAD_MAX_BYTES:
            raise serializers.ValidationError("File exceeds the attachment size limit.")
        return value


class AttachmentUploadSessionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    upload_url = serializers.URLField()
    headers = serializers.DictField(child=serializers.CharField())
    expires_in = serializers.IntegerField()
