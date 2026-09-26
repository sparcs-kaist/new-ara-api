from datetime import datetime
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.management.scripts import instagram_client, meal_instagram
from apps.core.management.scripts.meal_instagram import crawl_instagram_menu_photos, meal_time_of
from apps.meal.models import MealType, MenuPhoto, Restaurant
from tests.test_meal_photo import MEMORY_STORAGE

WINDOWS = {"BREAKFAST": ("07:00", "09:30"), "LUNCH": ("10:30", "13:30"), "DINNER": ("16:30", "19:00")}


def kst(*args):
    return timezone.make_aware(datetime(*args))


def node(post_id, taken_at, children=None):
    data = {"id": post_id, "taken_at_timestamp": int(taken_at.timestamp()), "display_url": f"https://img/{post_id}", "is_video": False}
    if children:
        data["edge_sidecar_to_children"] = {"edges": [{"node": child} for child in children]}
    return data


def profile_response(*nodes):
    res = MagicMock(status_code=200)
    res.json.return_value = {"data": {"user": {"edge_owner_to_timeline_media": {"edges": [{"node": n} for n in nodes]}}}}
    return res


class TestMealTimeOf(TestCase):
    def test_windows(self):
        assert meal_time_of(kst(2026, 9, 28, 11, 50), WINDOWS) == (datetime(2026, 9, 28).date(), MealType.LUNCH)
        assert meal_time_of(kst(2026, 9, 28, 13, 30), WINDOWS) is None
        assert meal_time_of(kst(2026, 9, 28, 7, 0), WINDOWS)[1] == MealType.BREAKFAST
        assert meal_time_of(kst(2026, 9, 28, 22, 0), WINDOWS) is None


class TestFetchRecentPosts(TestCase):
    def test_parses_carousel_and_skips_video(self):
        carousel = node("1", kst(2026, 9, 28, 11, 50), children=[
            {"display_url": "https://img/a", "is_video": False},
            {"display_url": "https://img/v", "is_video": True},
            {"display_url": "https://img/b", "is_video": False},
        ])
        video = {**node("2", kst(2026, 9, 28, 12)), "is_video": True}
        with patch.object(instagram_client.requests, "get", return_value=profile_response(carousel, video)):
            posts = instagram_client.fetch_recent_posts("gaon_kaist_n11")
        assert [(p.post_id, p.image_urls) for p in posts] == [("1", ("https://img/a", "https://img/b"))]

    def test_blocked_or_changed_returns_empty(self):
        blocked = MagicMock()
        blocked.raise_for_status.side_effect = requests.HTTPError("429")
        login_page = MagicMock(status_code=200)
        login_page.json.side_effect = ValueError("not json")
        changed = MagicMock(status_code=200)
        changed.json.return_value = {"data": {"user": None}}
        for res in (blocked, login_page, changed):
            with patch.object(instagram_client.requests, "get", return_value=res):
                assert instagram_client.fetch_recent_posts("gaon_kaist_n11") == []
        with patch.object(instagram_client.requests, "get", side_effect=requests.ConnectionError()):
            assert instagram_client.fetch_recent_posts("gaon_kaist_n11") == []


@override_settings(STORAGES=MEMORY_STORAGE, MEAL_PHOTO_WINDOWS=WINDOWS, MEAL_PHOTO_INSTAGRAM_ACCOUNTS={"gaon_kaist_n11": "fclt"})
class TestCrawlInstagramMenuPhotos(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(restaurant_name="카이마루", code="fclt")
        self.posts = [
            instagram_client.to_post(node("10", kst(2026, 9, 28, 11, 40), children=[
                {"display_url": "https://img/a", "is_video": False},
                {"display_url": "https://img/b", "is_video": False},
            ])),
            # 끼니 구간 밖
            instagram_client.to_post(node("11", kst(2026, 9, 28, 15, 0))),
        ]

    def crawl(self, now):
        with patch.object(meal_instagram, "fetch_recent_posts", return_value=self.posts) as fetch, \
                patch.object(meal_instagram, "download_image", return_value=b"img") as download:
            saved = crawl_instagram_menu_photos(now)
        return saved, fetch, download

    def test_saves_only_meal_window_posts_once(self):
        saved, _, _ = self.crawl(kst(2026, 9, 28, 11, 50))
        assert saved == 2
        photos = MenuPhoto.objects.order_by("source_post_id")
        assert [p.source_post_id for p in photos] == ["10_0", "10_1"]
        assert all(p.meal_time == "LUNCH" and p.is_official and p.created_by is None for p in photos)

        # 다시 돌거나 지운 뒤에도 다시 받지 않는다
        photos[0].delete()
        saved, _, download = self.crawl(kst(2026, 9, 28, 12, 0))
        assert saved == 0
        download.assert_not_called()

    def test_outside_window_does_not_request(self):
        saved, fetch, _ = self.crawl(kst(2026, 9, 28, 15, 0))
        assert saved == 0
        fetch.assert_not_called()
