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
    filename = serializers.CharField(
        max_length=255, help_text="S3에 직접 업로드할 원본 파일명 (브라우저의 File.name)."
    )
    alias = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="표시할 파일명. 생략하거나 비우면 원본 파일명을 사용합니다.",
    )
    size = serializers.IntegerField(
        min_value=1,
        max_value=S3_PUT_MAX_BYTES,
        help_text=(
            "원본 파일 크기 (바이트, 브라우저의 File.size). "
            "기본 최대 5GiB이며 배포 환경의 설정에 따라 더 낮을 수 있습니다."
        ),
    )

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
    id = serializers.UUIDField(
        help_text="완료 API에 사용할 업로드 세션 UUID. 게시글에 연결하는 Attachment.id와 다릅니다."
    )
    upload_url = serializers.URLField(help_text="원본 파일을 직접 PUT할 S3 업로드 URL.")
    headers = serializers.DictField(
        child=serializers.CharField(), help_text="S3 PUT 요청에 그대로 포함할 헤더."
    )
    expires_in = serializers.IntegerField(help_text="업로드 URL의 유효기간 (초).")
