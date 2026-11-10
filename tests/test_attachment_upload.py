from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from botocore.stub import Stubber
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models.attachment import Attachment, AttachmentUpload
from apps.user.models import UserProfile

UPLOAD_URL = "/api/attachments/uploads/"
SIZE = 150_000_000

pytestmark = pytest.mark.django_db


@pytest.fixture
def upload_api(settings):
    settings.AWS_ACCESS_KEY_ID = "testing"
    settings.AWS_SECRET_ACCESS_KEY = "testing"
    settings.AWS_S3_BUCKET_NAME = "ara-upload-test"
    settings.AWS_S3_PUBLIC_URL = "https://files.example.test/"
    client = authenticated_client("attachment-owner")
    s3 = default_storage.s3_connection
    with Stubber(s3) as stub:
        yield client, s3, stub
        stub.assert_no_pending_responses()


def authenticated_client(username):
    user = get_user_model().objects.create_user(username)
    UserProfile.objects.create(
        user=user, nickname=username, agree_terms_of_service_at=timezone.now()
    )
    client = APIClient()
    client.force_authenticate(user)
    return client


def start_upload(client):
    response = client.post(
        UPLOAD_URL, {"filename": "자료.ZIP", "size": SIZE}, format="json"
    )
    assert response.status_code == 201, response.data
    upload = AttachmentUpload.objects.get(pk=response.data["id"])
    return response, upload


def object_params(upload):
    return {"Bucket": "ara-upload-test", "Key": upload.file_name}


def completion_url(upload):
    return f"{UPLOAD_URL}{upload.pk}/complete/"


def expect_uploaded_object(stub, upload, **overrides):
    stub.add_response(
        "head_object",
        {
            "ContentLength": SIZE,
            "ContentType": "application/zip",
            "Metadata": {"ara-attachment-upload": str(upload.pk)},
            **overrides,
        },
        object_params(upload),
    )


def test_upload_signs_one_put_and_completion_returns_the_existing_attachment_shape(
    upload_api,
):
    client, s3, stub = upload_api
    with patch.object(
        s3, "generate_presigned_url", wraps=s3.generate_presigned_url
    ) as sign:
        response, upload = start_upload(client)

    sign.assert_called_once()
    assert sign.call_args.args == ("put_object",)
    assert sign.call_args.kwargs["Params"]["ContentLength"] == SIZE
    assert response["Cache-Control"] == "no-store"
    assert response.data["expires_in"] == 900
    headers = response.data["headers"]
    assert headers["If-None-Match"] == "*"
    assert headers["Content-Type"] == "application/zip"
    assert headers["x-amz-tagging"] == "ara-upload=pending"
    assert headers["x-amz-acl"] == "public-read"
    signed_url = urlsplit(response.data["upload_url"])
    assert signed_url.hostname.endswith(".amazonaws.com")
    assert signed_url.path.endswith(upload.file_name)
    signed_headers = parse_qs(signed_url.query)["X-Amz-SignedHeaders"][0].split(";")
    assert set(signed_headers) == {name.lower() for name in headers} | {
        "host",
        "content-length",
    }

    expect_uploaded_object(stub, upload)
    stub.add_response("delete_object_tagging", {}, object_params(upload))
    url = completion_url(upload)
    response = client.post(url)
    assert response.status_code == 200, response.data
    assert response.data["size"] == SIZE
    assert response.data["mimetype"] == "application/zip"
    assert response.data["alias"] == "자료.ZIP"
    attachment_url = f'/api/attachments/{response.data["id"]}/'
    assert client.get(attachment_url).data == response.data
    assert client.post(url).data == response.data
    assert Attachment.objects.count() == 1


def test_upload_rejects_invalid_input_and_other_users(upload_api):
    client, _, _ = upload_api
    assert APIClient().post(UPLOAD_URL, {}, format="json").status_code in {401, 403}
    for filename, size in [
        ("tool.exe", SIZE),
        ("../data.zip", SIZE),
        ("data.zip", 5 * 1024**3 + 1),
    ]:
        assert (
            client.post(
                UPLOAD_URL, {"filename": filename, "size": size}, format="json"
            ).status_code
            == 400
        )
    with override_settings(ATTACHMENT_UPLOAD_MAX_BYTES=SIZE - 1):
        assert (
            client.post(
                UPLOAD_URL, {"filename": "data.zip", "size": SIZE}, format="json"
            ).status_code
            == 400
        )
    _, upload = start_upload(client)
    other_client = authenticated_client("other-user")
    assert other_client.post(completion_url(upload)).status_code == 404


@pytest.mark.parametrize(
    "object_fields",
    [{"ContentLength": SIZE - 1}, {"ContentType": "text/html"}, {"Metadata": {}}],
)
def test_completion_rejects_an_object_that_does_not_match_the_session(
    upload_api, object_fields
):
    client, _, stub = upload_api
    _, upload = start_upload(client)
    expect_uploaded_object(stub, upload, **object_fields)

    assert client.post(completion_url(upload)).status_code == 409
    assert Attachment.objects.count() == 0


def test_completion_handles_missing_object_and_recovers_after_s3_failure(upload_api):
    client, _, stub = upload_api
    _, upload = start_upload(client)
    params = object_params(upload)
    url = completion_url(upload)
    stub.add_client_error(
        "head_object",
        service_error_code="404",
        http_status_code=404,
        expected_params=params,
    )
    assert client.post(url).status_code == 409

    expect_uploaded_object(stub, upload)
    stub.add_client_error(
        "delete_object_tagging",
        service_error_code="InternalError",
        http_status_code=500,
        expected_params=params,
    )
    assert client.post(url).status_code == 503
    upload.refresh_from_db()
    assert upload.completed_at is None
    assert Attachment.objects.count() == 0

    expect_uploaded_object(stub, upload)
    stub.add_response("delete_object_tagging", {}, params)
    assert client.post(url).status_code == 200
    assert Attachment.objects.count() == 1


def test_completion_expires_unfinished_sessions(upload_api):
    client, _, _ = upload_api
    _, upload = start_upload(client)
    AttachmentUpload.objects.filter(pk=upload.pk).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    assert client.post(completion_url(upload)).status_code == 410


def test_legacy_attachment_post_accepts_a_file(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    }
    client = authenticated_client("legacy-uploader")
    file = SimpleUploadedFile(
        "small.zip", b"file bytes", content_type="application/zip"
    )

    response = client.post("/api/attachments/", {"file": file}, format="multipart")
    assert response.status_code == 201, response.data
    assert response.data["size"] == len(b"file bytes")
    assert AttachmentUpload.objects.count() == 0
