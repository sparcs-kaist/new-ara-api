from datetime import datetime, time, timedelta

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.meal.models import Store, StoreEvent, StoreMenu, StoreNotice, StoreStaff
from tests.conftest import RequestSetting, TestCase
from tests.test_meal_photo import MEMORY_STORAGE, make_image


HOURS = {
    "mon": [{"open": "09:00", "close": "14:00"}, {"open": "15:00", "close": "18:00"}],
    "sun": [],
}


def kst(*args):
    return timezone.make_aware(datetime(*args))


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
        assert self.http_request(self.user2, "patch", path, {"name": "x"}).status_code == 403
        res = self.http_request(self.user, "patch", path, {"hours": HOURS, "name": "바꾼 이름", "zone": "WEST", "is_active": False})
        assert res.status_code == 200, res.data
        assert res.data["hours"] == HOURS
        assert (res.data["name"], res.data["zone"]) == ("바꾼 이름", "WEST")
        # 운영 여부는 운영진만
        assert res.data["is_active"] is True

    def test_hours_validation(self):
        path = f"stores/{self.store.id}"
        for bad in ["9-18", {"monday": []}, {"mon": [{"open": "18:00", "close": "09:00"}]}, {"mon": [{"open": "9:00", "close": "18:00"}]}]:
            assert self.http_request(self.user, "patch", path, {"hours": bad}).status_code == 400, bad

    def test_open_state(self):
        self.store.hours = HOURS
        self.store.save()
        # 2026-09-28 은 월요일
        assert self.store.open_state(kst(2026, 9, 28, 10)) == {"is_open": True, "open_note": "14:00까지 영업", "today_hours": "09:00–14:00, 15:00–18:00"}
        assert self.store.open_state(kst(2026, 9, 28, 14, 30))["open_note"] == "15:00 영업 시작"
        assert self.store.open_state(kst(2026, 9, 28, 19))["open_note"] == "영업 종료"
        assert self.store.open_state(kst(2026, 9, 27, 12)) == {"is_open": False, "open_note": "오늘 휴무", "today_hours": None}

        # 일요일 임시 영업
        StoreEvent.objects.create(
            store=self.store, kind="OPEN", starts_at=kst(2026, 9, 27, 0), ends_at=kst(2026, 9, 27, 23),
            open_time=time(11), close_time=time(15),
        )
        assert self.store.open_state(kst(2026, 9, 27, 12))["open_note"] == "15:00까지 영업"
        # 휴무가 이긴다
        StoreEvent.objects.create(store=self.store, kind="CLOSED", starts_at=kst(2026, 9, 26, 0), ends_at=kst(2026, 9, 28, 23), reason="재료 소진")
        state = self.store.open_state(kst(2026, 9, 27, 12))
        assert state["is_open"] is False
        assert state["open_note"] == "임시 휴무 · 재료 소진 (09/28까지)"

    def test_events_crud(self):
        path = f"stores/{self.store.id}/events"
        now = timezone.now()
        assert self.http_request(self.user2, "post", path, {"kind": "CLOSED", "starts_at": now.isoformat()}).status_code == 403
        res = self.http_request(self.user, "post", path, {"kind": "CLOSED", "starts_at": now.isoformat()})
        assert res.status_code == 201, res.data
        event_id = res.data["id"]
        # OPEN 은 시간이 필요하다
        assert self.http_request(self.user, "post", path, {"kind": "OPEN", "starts_at": now.isoformat()}).status_code == 400
        res = self.http_request(self.user, "post", path, {"kind": "OPEN", "starts_at": now.isoformat(), "open": "11:00", "close": "15:00"})
        assert (res.data["open"], res.data["close"]) == ("11:00", "15:00")
        StoreEvent.objects.create(store=self.store, kind="CLOSED", starts_at=now - timedelta(days=3), ends_at=now - timedelta(days=1))

        # 끝난 이벤트는 안 보인다
        assert len(self.http_request(self.user, "get", path).data) == 2
        detail = self.http_request(self.user2, "get", f"stores/{self.store.id}").data
        assert detail["is_open"] is False and detail["open_note"] == "임시 휴무"

        res = self.http_request(self.user, "patch", f"{path}/{event_id}", {"reason": "휴가"})
        assert res.data["reason"] == "휴가"
        assert self.http_request(self.user, "delete", f"{path}/{event_id}").status_code == 204
        assert self.http_request(self.user2, "get", f"stores/{self.store.id}").data["open_note"] != "임시 휴무"

    def test_signature_menus_in_list(self):
        for i in range(4):
            StoreMenu.objects.create(store=self.store, name=f"대표{i}", is_signature=True, order=i + 2)
        res = self.http_request(self.user2, "get", "stores")
        cafe = next(s for s in res.data if s["id"] == self.store.id)
        assert len(cafe["signature_menus"]) == 3
        assert {"is_open", "open_note", "today_hours", "hours_note"} <= set(cafe)

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
        assert self.http_request(self.user, "patch", f"stores/{self.store.id}", {"hours_note": "시험기간 연장"}).status_code == 200
        assert self.http_request(self.admin, "delete", f"{path}/{self.user.id}").status_code == 204
        assert self.http_request(self.user, "patch", f"stores/{self.store.id}", {"hours_note": "x"}).status_code == 403

    def test_user_search_and_restaurant_edit(self):
        from apps.meal.models import Restaurant

        res = self.http_request(self.admin, "get", "ops/users", querystring=f"q={self.user2.profile.nickname}")
        assert self.user2.id in [u["id"] for u in res.data]

        restaurant = Restaurant.objects.create(restaurant_name="동맛골 1층", code="east1")
        res = self.http_request(self.admin, "patch", f"ops/restaurants/{restaurant.id}", {"display_name": "동맛골 1층", "is_active": False})
        assert res.status_code == 200
        assert res.data["display_name"] == "동맛골 1층"

    def test_staff_deletes_any_menu_photo(self):
        from apps.meal.models import MenuPhoto, Restaurant
        from tests.test_meal_photo import make_image

        restaurant = Restaurant.objects.create(restaurant_name="카이마루")
        photo = MenuPhoto.objects.create(
            restaurant=restaurant, date="2026-09-26", meal_time="LUNCH", image=make_image(), created_by=self.user,
        )
        assert self.http_request(self.user2, "delete", f"meal/photos/{photo.id}").status_code == 403
        assert self.http_request(self.admin, "delete", f"meal/photos/{photo.id}").status_code == 204
