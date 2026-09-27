import json
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


def pk_at(moment, seq=1):
    return str(((int(moment.timestamp() * 1000) - instagram_client.INSTAGRAM_EPOCH_MS) << 23) + seq)


def node(moment, media_type=1, seq=1):
    return {"pk": pk_at(moment, seq), "code": "x", "display_uri": f"https://img/{seq}", "media_type": media_type, "caption": None}


# 프로필 페이지에 박혀 오는 모양 (2026-09 실제 페이지 기준)
def profile_page(*nodes):
    data = {"require": [["ScheduledServerJS", "handle", None, [{"__bbox": {"require": [["RelayPrefetchedStreamCache", "next", [], [
        "adp_PolarisLoggedOutDesktopWWWProfilePostsTabContentQueryRelayPreloader",
        {"__bbox": {"complete": True, "result": {"data": {"xig_user_by_username": {
            "polaris_ordered_timeline_connection": {"edges": [{"node": n} for n in nodes]},
        }}}}},
    ]]]}}]]]}
    res = MagicMock(status_code=200)
    res.text = f'<html><script type="application/json" data-sjs>{json.dumps(data)}</script></html>'
    return res


class TestMealTimeOf(TestCase):
    def test_windows(self):
        assert meal_time_of(kst(2026, 9, 28, 11, 50), WINDOWS) == (datetime(2026, 9, 28).date(), MealType.LUNCH)
        assert meal_time_of(kst(2026, 9, 28, 13, 30), WINDOWS) is None
        assert meal_time_of(kst(2026, 9, 28, 7, 0), WINDOWS)[1] == MealType.BREAKFAST
        assert meal_time_of(kst(2026, 9, 28, 22, 0), WINDOWS) is None


class TestFetchRecentPosts(TestCase):
    def test_parses_page_and_skips_video(self):
        page = profile_page(node(kst(2026, 9, 23, 11, 45), seq=1), node(kst(2026, 9, 23, 12), media_type=2, seq=2), node(kst(2026, 9, 17, 11, 13), media_type=8, seq=3))
        with patch.object(instagram_client.requests, "get", return_value=page):
            posts = instagram_client.fetch_recent_posts("gaon_kaist_n11")
        assert [p.image_urls for p in posts] == [("https://img/1",), ("https://img/3",)]
        assert timezone.localtime(posts[0].taken_at).strftime("%m-%d %H:%M") == "09-23 11:45"

    def test_real_post_id_time(self):
        # 실제 게시물 DdnRI6kPdVi (카이마루 중식)
        post = instagram_client.to_post({"pk": "3992234974118794594", "display_uri": "u"})
        assert timezone.localtime(post.taken_at).strftime("%Y-%m-%d %H:%M") == "2026-09-23 11:45"

    def test_blocked_or_changed_returns_empty(self):
        blocked = MagicMock()
        blocked.raise_for_status.side_effect = requests.HTTPError("429")
        login_page = MagicMock(status_code=200, text="<html>login</html>")
        broken = MagicMock(status_code=200, text='<script type="application/json">{"polaris_ordered_timeline_connection": </script>')
        for res in (blocked, login_page, broken):
            with patch.object(instagram_client.requests, "get", return_value=res):
                assert instagram_client.fetch_recent_posts("gaon_kaist_n11") == []
        with patch.object(instagram_client.requests, "get", side_effect=requests.ConnectionError()):
            assert instagram_client.fetch_recent_posts("gaon_kaist_n11") == []


@override_settings(STORAGES=MEMORY_STORAGE, MEAL_PHOTO_WINDOWS=WINDOWS)
class TestCrawlInstagramMenuPhotos(TestCase):
    def setUp(self):
        self.restaurant = Restaurant.objects.create(restaurant_name="카이마루", code="fclt")
        self.posts = [
            instagram_client.to_post(node(kst(2026, 9, 28, 11, 40), seq=1)),
            instagram_client.to_post(node(kst(2026, 9, 28, 11, 41), seq=2)),
            # 끼니 구간 밖
            instagram_client.to_post(node(kst(2026, 9, 28, 15, 0), seq=3)),
        ]

    def crawl(self, now):
        with patch.object(meal_instagram, "fetch_recent_posts", return_value=self.posts) as fetch, \
                patch.object(meal_instagram, "download_image", return_value=b"img") as download:
            saved = crawl_instagram_menu_photos(now)
        return saved, fetch, download

    def test_saves_only_meal_window_posts_once(self):
        saved, _, _ = self.crawl(kst(2026, 9, 28, 11, 50))
        assert saved == 2
        photos = list(MenuPhoto.objects.order_by("source_post_id"))
        assert sorted(p.source_post_id for p in photos) == sorted(f"{p.post_id}_0" for p in self.posts[:2])
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
