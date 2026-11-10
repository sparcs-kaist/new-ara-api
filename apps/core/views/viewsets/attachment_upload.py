import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import timedelta
from mimetypes import guess_type
from pathlib import PurePath
from typing import Any

from botocore.client import BaseClient
from botocore.exceptions import BotoCoreError, ClientError
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls.converters import UUIDConverter
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.models.attachment import Attachment, AttachmentUpload
from apps.core.serializers.attachment import (
    AttachmentSerializer,
    AttachmentUploadSessionSerializer,
    StartAttachmentUploadSerializer,
)

logger = logging.getLogger(__name__)
UPLOAD_URL_TTL = 15 * 60
UPLOAD_SESSION_TTL = timedelta(hours=24)
UPLOAD_ID_METADATA = "ara-attachment-upload"
PENDING_UPLOAD_TAG = "ara-upload=pending"


class UploadConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The file has not reached S3 yet."


class UploadGone(APIException):
    status_code = status.HTTP_410_GONE
    default_detail = "The upload session has expired."


class UploadStorageUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Attachment storage is temporarily unavailable. Retry the request."


@contextmanager
def handle_s3_errors() -> Iterator[None]:
    try:
        yield
    except ClientError as exc:
        logger.warning("S3 attachment upload failed: %s", exc.response["Error"]["Code"])
        raise UploadStorageUnavailable() from exc
    except BotoCoreError as exc:
        logger.warning("S3 attachment upload failed: %s", type(exc).__name__)
        raise UploadStorageUnavailable() from exc


def put_request_headers(client: BaseClient, params: dict[str, Any]) -> dict[str, str]:
    members = client.meta.service_model.operation_model("PutObject").input_shape.members
    headers = {}
    for name, value in params.items():
        field = members[name].serialization
        # The browser supplies Content-Length from the raw File body.
        if field.get("location") == "header" and name != "ContentLength":
            headers[field["name"]] = str(value)
    headers.update(
        {f"x-amz-meta-{name}": str(value) for name, value in params["Metadata"].items()}
    )
    return headers


# 브라우저가 S3로 파일을 직접 전송하도록 URL 발급과 완료 확인을 담당하는 API.
# 대용량 파일이 Ara API를 경유하지 않아 Cloudflare의 업로드 크기 제한을 피한다.
class AttachmentUploadViewSet(viewsets.GenericViewSet):
    queryset = AttachmentUpload.objects.all()
    serializer_class = StartAttachmentUploadSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (JSONParser,)
    lookup_value_regex = UUIDConverter.regex

    def get_queryset(self) -> QuerySet[AttachmentUpload]:
        return self.queryset.filter(owner_id=self.request.user.pk)

    @extend_schema(
        tags=["attachments - S3 직접 업로드"],
        summary="S3 직접 업로드 URL 발급 (Cloudflare 업로드 제한 대응)",
        description=(
            "Cloudflare의 업로드 크기 제한에 대응하는 S3 직접 업로드 API입니다. "
            "파일명과 크기를 JSON으로 보내면 업로드 세션 ID, S3 업로드 URL과 요청 헤더를 반환합니다.\n\n"
            "1. 이 API로 업로드 URL을 발급받습니다.\n"
            "2. 반환된 URL과 헤더로 S3에 원본 파일을 PUT합니다. "
            "파일 본문은 Ara API와 Cloudflare를 경유하지 않습니다. "
            "FormData로 감싸거나 Ara 인증 헤더를 추가하지 마세요.\n"
            "3. S3 전송 성공 후 `/api/attachments/uploads/{id}/complete/`를 호출합니다.\n\n"
            "업로드 URL은 15분 동안 유효합니다. "
            "기존 `POST /api/attachments/`는 Ara 서버가 파일을 받는 업로드 방식입니다."
        ),
        responses={201: AttachmentUploadSessionSerializer},
    )
    def create(self, request: Request) -> Response:
        # S3 직접 업로드에 사용할 URL과 요청 헤더를 발급한다.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        filename = data["filename"]
        mimetype, _ = guess_type(filename, strict=False)
        upload = AttachmentUpload(
            owner=request.user,
            alias=data.get("alias") or filename,
            size=data["size"],
            mimetype=mimetype or "application/octet-stream",
        )
        extension = PurePath(filename).suffix.lower()
        upload.file_name = f"files/direct-uploads/{upload.pk}{extension}"

        with handle_s3_errors():
            client = default_storage.s3_connection
            # Match the bucket, key prefix, ACL and cache settings used by FileField.
            params = default_storage._object_put_params(upload.file_name)
            params["Metadata"][UPLOAD_ID_METADATA] = str(upload.pk)
            params.update(
                ContentLength=upload.size,
                ContentType=upload.mimetype,
                IfNoneMatch="*",
                Tagging=PENDING_UPLOAD_TAG,
            )
            upload_url = client.generate_presigned_url(
                "put_object", Params=params, ExpiresIn=UPLOAD_URL_TTL
            )
            headers = put_request_headers(client, params)

        upload.save(force_insert=True)
        return Response(
            {
                "id": str(upload.pk),
                "upload_url": upload_url,
                "headers": headers,
                "expires_in": UPLOAD_URL_TTL,
            },
            status=status.HTTP_201_CREATED,
            headers={"Cache-Control": "no-store"},
        )

    @extend_schema(
        tags=["attachments - S3 직접 업로드"],
        summary="S3 직접 업로드 완료 및 첨부파일 등록",
        description=(
            "S3 직접 업로드가 성공한 뒤, URL 발급 시 받은 업로드 세션 ID로 호출합니다. "
            "요청 본문은 필요하지 않습니다.\n\n"
            "S3 파일의 크기, Content-Type과 업로드 식별 정보를 확인한 뒤 "
            "기존 API와 동일한 형식의 Attachment를 반환합니다. "
            "게시글의 `attachments`에는 이 응답의 `id`를 사용하며, "
            "업로드 세션 UUID를 사용하지 않습니다.\n\n"
            "같은 완료 요청을 반복해도 동일한 Attachment를 반환합니다. "
            "미완료 세션은 생성 후 24시간이 지나면 만료됩니다."
        ),
        request=None,
        responses={200: AttachmentSerializer},
    )
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request: Request, pk: str) -> Response:
        # S3 업로드 결과를 확인하고 정식 Attachment로 등록한다.
        upload = get_object_or_404(self.get_queryset().select_for_update(), pk=pk)
        if upload.completed_at is not None:
            attachment = get_object_or_404(Attachment, pk=upload.attachment_id)
        else:
            attachment = self.register_attachment(upload)
        return Response(
            AttachmentSerializer(attachment, context=self.get_serializer_context()).data
        )

    def register_attachment(self, upload: AttachmentUpload) -> Attachment:
        if timezone.now() >= upload.created_at + UPLOAD_SESSION_TTL:
            raise UploadGone()

        with handle_s3_errors():
            client = default_storage.s3_connection
            object_params = default_storage._object_params(upload.file_name)
            try:
                obj = client.head_object(**object_params)
            except ClientError as exc:
                if exc.response["Error"]["Code"] in {"404", "NotFound", "NoSuchKey"}:
                    raise UploadConflict() from exc
                raise
            if (
                obj.get("Metadata", {}).get(UPLOAD_ID_METADATA) != str(upload.pk)
                or obj["ContentLength"] != upload.size
                or obj.get("ContentType") != upload.mimetype
            ):
                raise UploadConflict(
                    "The uploaded object does not match the upload session."
                )

            attachment = Attachment.objects.create(
                file=upload.file_name,
                alias=upload.alias,
                size=upload.size,
                mimetype=upload.mimetype,
            )
            upload.attachment = attachment
            upload.completed_at = timezone.now()
            upload.save(update_fields=["attachment", "completed_at"])
            # Keep incomplete uploads eligible for S3 expiry until registration succeeds.
            client.delete_object_tagging(**object_params)

        return attachment
