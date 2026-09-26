import pytest

from apps.core.management.scripts.meal_crawler import _crawl_and_save_course_restaurant, _get_or_create_restaurant
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
