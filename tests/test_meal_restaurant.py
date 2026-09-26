import pytest

from apps.core.management.scripts.meal_crawler import (
    RESTAURANT_CODE_TO_NAME,
    _crawl_and_save_course_restaurant,
    _get_or_create_restaurant,
)
from apps.meal.models import Restaurant
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client")
class TestRestaurant(TestCase, RequestSetting):
    def test_crawler_finds_by_code_even_after_rename(self):
        # code 가 없던 기존 식당은 이름으로 찾아 code 를 채운다
        old = Restaurant.objects.create(restaurant_name="카이마루")
        assert _get_or_create_restaurant("fclt", "카이마루") == old
        old.refresh_from_db()
        assert old.code == "fclt"

        Restaurant.objects.filter(pk=old.pk).update(restaurant_name="다른 이름")
        assert _get_or_create_restaurant("fclt", "카이마루").pk == old.pk
        assert Restaurant.objects.count() == 1

    def test_inactive_restaurant_is_not_crawled_or_listed(self):
        Restaurant.objects.create(restaurant_name="카이마루", code="fclt", is_active=False)
        Restaurant.objects.create(restaurant_name="서맛골", code="west")
        assert _crawl_and_save_course_restaurant("fclt", "2026-09-26") == "skipped"

        res = self.http_request(self.user, "get", "meal/restaurants")
        assert res.status_code == 200
        assert [r["code"] for r in res.data] == ["west"]
        assert res.data[0]["display_name"] == "서맛골"

    def test_display_name_is_filled_once(self):
        restaurant = _get_or_create_restaurant("east1", "동맛골 1층")
        assert restaurant.display_name == "동맛골 1층 (학생식당)"
        # admin 에서 바꾼 값은 크롤러가 덮어쓰지 않는다
        Restaurant.objects.filter(pk=restaurant.pk).update(display_name="바꾼 이름")
        assert _get_or_create_restaurant("east1", "동맛골 1층").display_name == "바꾼 이름"

    def test_legacy_row_gets_code(self):
        # 예전에 이름으로만 만든 식당 (prod id 3, 4) 을 그대로 이어 쓴다
        legacy = Restaurant.objects.create(restaurant_name="동맛골 2층")
        assert _get_or_create_restaurant("east2", RESTAURANT_CODE_TO_NAME["east2"]).pk == legacy.pk
        assert Restaurant.objects.filter(restaurant_name__startswith="동맛골").count() == 1
