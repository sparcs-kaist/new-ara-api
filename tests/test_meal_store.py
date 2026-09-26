from datetime import timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.meal.models import Store, StoreMenu, StoreNotice, StoreStaff
from tests.conftest import RequestSetting, TestCase
from tests.test_meal_photo import MEMORY_STORAGE, make_image


@override_settings(STORAGES=MEMORY_STORAGE)
@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestStore(TestCase, RequestSetting):
    # user = 직원, user2 = 일반 사용자
    def setUp(self):
        self.store = Store.objects.create(name="카페", zone="EAST", location="N11 1층")
        Store.objects.create(name="분식", zone="WEST")
        Store.objects.create(name="닫은 가게", zone="EAST", is_active=False)
        StoreStaff.objects.create(store=self.store, user=self.user)
        StoreMenu.objects.create(store=self.store, name="아메리카노", price=2000, order=1)
        StoreNotice.objects.create(store=self.store, title="오늘 조기 마감")
        StoreNotice.objects.create(store=self.store, title="지난 공지", ends_at=timezone.now() - timedelta(days=1))

    def test_public_list_and_detail(self):
        self.api_client.force_authenticate(user=None)
        res = self.api_client.get("/api/stores/", {"zone": "EAST"})
        assert [s["name"] for s in res.data] == ["카페"]

        res = self.api_client.get(f"/api/stores/{self.store.id}/")
        assert res.status_code == 200
        assert [m["name"] for m in res.data["menus"]] == ["아메리카노"]
        assert [n["title"] for n in res.data["notices"]] == ["오늘 조기 마감"]
        assert res.data["is_staff"] is False

    def test_only_staff_edits(self):
        path = f"stores/{self.store.id}"
        assert self.http_request(self.user2, "patch", path, {"hours": "9-18"}).status_code == 403
        res = self.http_request(self.user, "patch", path, {"hours": "9-18", "name": "바꾼 이름"})
        assert res.status_code == 200
        assert res.data["hours"] == "9-18"
        # 이름은 운영진만 (직원 API 로는 안 바뀐다)
        assert res.data["name"] == "카페"

    def test_menu_crud_with_photo_and_sold_out(self):
        self.api_client.force_authenticate(user=self.user)
        res = self.api_client.post(f"/api/stores/{self.store.id}/menus/", {
            "name": "라떼", "price": 3000, "section": "커피", "photo": make_image(),
        }, format="multipart")
        assert res.status_code == 201, res.data
        menu_id = res.data["id"]
        assert res.data["photo"]

        res = self.http_request(self.user, "patch", f"stores/{self.store.id}/menus/{menu_id}", {"is_sold_out": True})
        assert res.data["is_sold_out"] is True
        assert self.http_request(self.user2, "patch", f"stores/{self.store.id}/menus/{menu_id}", {"is_sold_out": False}).status_code == 403
        assert self.http_request(self.user, "delete", f"stores/{self.store.id}/menus/{menu_id}").status_code == 204

    def test_notice_and_mine(self):
        res = self.http_request(self.user, "post", f"stores/{self.store.id}/notices", {"title": "재료 소진"})
        assert res.status_code == 201
        assert self.http_request(self.user, "get", "stores/mine").data == {"store_ids": [self.store.id]}
        assert self.http_request(self.user2, "get", "stores/mine").data == {"store_ids": []}


@override_settings(STORAGES=MEMORY_STORAGE)
@pytest.mark.usefixtures("set_admin_client", "set_user_client", "set_user_client2")
class TestOps(TestCase, RequestSetting):
    def setUp(self):
        from apps.user.models import UserProfile

        type(self.admin).objects.filter(pk=self.admin.pk).update(is_staff=True)
        self.admin.refresh_from_db()
        self.store = Store.objects.create(name="카페", zone="EAST")
        self.UserProfile = UserProfile

    def test_only_staff(self):
        assert self.http_request(self.user, "get", "ops/stores").status_code == 403
        res = self.http_request(self.admin, "post", "ops/stores", {"name": "분식", "zone": "WEST"})
        assert res.status_code == 201
        res = self.http_request(self.admin, "patch", f"ops/stores/{res.data['id']}", {"is_active": False})
        assert res.data["is_active"] is False

    def test_assign_staff_needs_group_confirmation(self):
        path = f"ops/stores/{self.store.id}/staff"
        res = self.http_request(self.admin, "post", path, {"user_id": self.user.id})
        assert res.status_code == 400
        assert res.data["code"] == "group_required"
        assert not StoreStaff.objects.exists()

        res = self.http_request(self.admin, "post", path, {"user_id": self.user.id, "grant_group": True})
        assert res.status_code == 201
        self.user.profile.refresh_from_db()
        assert self.user.profile.group == self.UserProfile.UserGroup.STORE_EMPLOYEE
        assert [s["id"] for s in self.http_request(self.admin, "get", path).data] == [self.user.id]

        # 지정된 계정은 자기 업체를 고칠 수 있다
        assert self.http_request(self.user, "patch", f"stores/{self.store.id}", {"hours": "9-18"}).status_code == 200
        assert self.http_request(self.admin, "delete", f"{path}/{self.user.id}").status_code == 204
        assert self.http_request(self.user, "patch", f"stores/{self.store.id}", {"hours": "x"}).status_code == 403

    def test_user_search_and_restaurant_edit(self):
        from apps.meal.models import Restaurant

        res = self.http_request(self.admin, "get", "ops/users", querystring=f"q={self.user2.profile.nickname}")
        assert self.user2.id in [u["id"] for u in res.data]

        restaurant = Restaurant.objects.create(restaurant_name="동맛골(동측학생식당)", code="east1")
        res = self.http_request(self.admin, "patch", f"ops/restaurants/{restaurant.id}", {"display_name": "동맛골 1층", "is_active": False})
        assert res.status_code == 200
        assert res.data["display_name"] == "동맛골 1층"

    def test_me_has_is_staff(self):
        self.api_client.force_authenticate(user=self.admin)
        assert self.api_client.get("/api/me").data["is_staff"] is True

    def test_staff_deletes_any_menu_photo(self):
        from apps.meal.models import MenuPhoto, Restaurant
        from tests.test_meal_photo import make_image

        restaurant = Restaurant.objects.create(restaurant_name="카이마루")
        photo = MenuPhoto.objects.create(
            restaurant=restaurant, date="2026-09-26", meal_time="LUNCH", image=make_image(), created_by=self.user,
        )
        assert self.http_request(self.user2, "delete", f"meal/photos/{photo.id}").status_code == 403
        assert self.http_request(self.admin, "delete", f"meal/photos/{photo.id}").status_code == 204
