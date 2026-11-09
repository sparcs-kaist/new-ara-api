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


class AttachmentUploadViewSet(viewsets.GenericViewSet):
    queryset = AttachmentUpload.objects.all()
    serializer_class = StartAttachmentUploadSerializer
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (JSONParser,)
    lookup_value_regex = UUIDConverter.regex

    def get_queryset(self) -> QuerySet[AttachmentUpload]:
        return self.queryset.filter(owner_id=self.request.user.pk)

    @extend_schema(responses={201: AttachmentUploadSessionSerializer})
    def create(self, request: Request) -> Response:
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

    @extend_schema(request=None, responses={200: AttachmentSerializer})
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def complete(self, request: Request, pk: str) -> Response:
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
