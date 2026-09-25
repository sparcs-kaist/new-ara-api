import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.meal.models import MenuPhoto, Restaurant
from apps.user.models import UserProfile
from tests.conftest import TestCase

# 업로드가 S3 로 가지 않게 메모리 저장소를 쓴다
MEMORY_STORAGE = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
}


def make_image(name="photo.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(STORAGES=MEMORY_STORAGE)
@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestMenuPhoto(TestCase):
    def setUp(self):
        self.restaurant, _ = Restaurant.objects.get_or_create(restaurant_name="카이마루")

    def upload(self, user, comment=""):
        self.api_client.force_authenticate(user=user)
        return self.api_client.post("/api/meal/photos/", {
            "restaurant_id": self.restaurant.id, "date": "20260925", "meal_time": "LUNCH",
            "image": make_image(), "comment": comment,
        }, format="multipart")

    def list_photos(self):
        self.api_client.force_authenticate(user=None)
        return self.api_client.get("/api/meal/photos/", {"restaurant_id": self.restaurant.id, "date": "20260925"})

    def test_upload_with_comment_and_list(self):
        res = self.upload(self.user, comment="오늘 카레 맛있어요")
        assert res.status_code == 201, res.data
        assert res.data["comment"] == "오늘 카레 맛있어요"
        assert res.data["is_official"] is False
        assert res.data["is_mine"] is True

        res = self.list_photos()
        assert res.status_code == 200
        assert len(res.data["results"]) == 1

    def test_limit_per_meal(self):
        for _ in range(3):
            assert self.upload(self.user).status_code == 201
        assert self.upload(self.user).status_code == 400

    def test_store_employee_photo_is_official_and_first(self):
        self.upload(self.user)
        UserProfile.objects.filter(user=self.user2).update(group=UserProfile.UserGroup.STORE_EMPLOYEE)
        self.upload(self.user2)
        self.upload(self.user)

        results = self.list_photos().data["results"]
        assert results[0]["is_official"] is True
        assert [r["is_official"] for r in results[1:]] == [False, False]

    def test_only_owner_deletes(self):
        photo_id = self.upload(self.user).data["id"]
        self.api_client.force_authenticate(user=self.user2)
        assert self.api_client.delete(f"/api/meal/photos/{photo_id}/").status_code == 403
        self.api_client.force_authenticate(user=self.user)
        assert self.api_client.delete(f"/api/meal/photos/{photo_id}/").status_code == 204
        assert not MenuPhoto.objects.filter(pk=photo_id).exists()
