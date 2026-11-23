from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from apps.core.models import Article
from apps.kaist.models import Post
from apps.kaist.portal import crawler, worker
from apps.kaist.portal.crawler import (
    Crawler,
    DeletedPostException,
    SessionExpiredException,
)
from apps.kaist.portal.worker import Worker


class PortalSessionTest(SimpleTestCase):
    def setUp(self):
        session = requests.Session()
        self.addCleanup(session.close)
        session_patch = patch.object(Crawler, "_session", session)
        session_patch.start()
        self.addCleanup(session_patch.stop)

        redis_patch = patch.object(crawler.redis, "get", return_value=b"redis-session")
        self.redis_get = redis_patch.start()
        self.addCleanup(redis_patch.stop)

        env_patch = patch.object(crawler, "PORTAL_JSESSIONID", "env-session")
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def cookie_header(self):
        request = requests.Request(
            "GET", "https://portal.kaist.ac.kr/wz/api/board/recents/123"
        )
        return Crawler._session.prepare_request(request).headers.get("Cookie")

    def test_refresh_removes_stale_domain_cookies_without_logging_credentials(self):
        Crawler._session.cookies.set("JSESSIONID", "old-session")
        Crawler._session.cookies.set(
            "JSESSIONID", "stale-domain-session", domain="portal.kaist.ac.kr"
        )
        Crawler._session.cookies.set(
            "JSESSIONID", "stale-path-session", domain="portal.kaist.ac.kr", path="/wz"
        )

        with self.assertLogs("ara_logger", level="INFO") as logs:
            Crawler.update_session_id()

        self.assertEqual(self.cookie_header(), "JSESSIONID=redis-session")
        self.assertNotIn("redis-session", "\n".join(logs.output))

    def test_missing_or_empty_redis_cookie_uses_environment(self):
        for stored in (None, b""):
            with self.subTest(stored=stored):
                self.redis_get.return_value = stored
                Crawler.update_session_id()
                self.assertEqual(self.cookie_header(), "JSESSIONID=env-session")

    def test_missing_credentials_raise_session_expired(self):
        for stored in (None, b""):
            with self.subTest(stored=stored):
                self.redis_get.return_value = stored
                with patch.object(crawler, "PORTAL_JSESSIONID", ""):
                    with self.assertRaises(SessionExpiredException):
                        Crawler.update_session_id()

    def test_each_batch_uses_latest_redis_cookie_on_its_first_request(self):
        post = Post(id=123, next_post_id=None)
        response = requests.Response()
        response.status_code = 200
        response.headers["Content-Type"] = "application/json"
        response._content = b"{}"
        headers = []

        def send(request, **kwargs):
            headers.append(request.headers.get("Cookie"))
            return response

        self.redis_get.side_effect = [b"first-session", b"second-session"]
        with (
            patch.object(Worker, "get_latest_saved_post", return_value=post),
            patch.object(worker, "CrawlIterator", return_value=(post,)),
            patch.object(Crawler, "_parse_response", return_value=post),
            patch.object(Crawler._session, "send", side_effect=send),
        ):
            self.assertEqual(Worker.fetch_from_the_latest(32, False), [post])
            Crawler._session.cookies.set(
                "JSESSIONID", "stale-server-session", domain="portal.kaist.ac.kr"
            )
            self.assertEqual(Worker.fetch_from_the_latest(32, False), [post])

        self.assertEqual(
            headers, ["JSESSIONID=first-session", "JSESSIONID=second-session"]
        )

    def test_single_post_refreshes_cookie_before_request(self):
        Crawler._session.cookies.set("JSESSIONID", "old-session")

        def get_post(post_id):
            self.assertEqual(self.cookie_header(), "JSESSIONID=redis-session")
            raise DeletedPostException()

        with patch.object(Crawler, "get_post", side_effect=get_post):
            Worker.fetch_and_save_single(123)

    def test_retry_replaces_cookies_added_by_failed_response(self):
        Crawler._session.cookies.set("JSESSIONID", "old-session")
        post = Post(id=123)
        headers = []

        def send(request, **kwargs):
            headers.append(request.headers.get("Cookie"))
            response = requests.Response()
            response.status_code = 200
            if len(headers) == 1:
                response.headers["Content-Type"] = "text/html"
                response._content = b"<html>Login required</html>"
                Crawler._session.cookies.set(
                    "JSESSIONID", "stale-server-session", domain="portal.kaist.ac.kr"
                )
            else:
                response.headers["Content-Type"] = "application/json"
                response._content = b"{}"
            return response

        with (
            patch.object(Crawler._session, "send", side_effect=send),
            patch.object(Crawler, "_parse_response", return_value=post),
        ):
            self.assertIs(Crawler.get_post(123), post)

        self.assertEqual(
            headers, ["JSESSIONID=old-session", "JSESSIONID=redis-session"]
        )

    def test_batch_reports_missing_credentials_before_fetching(self):
        self.redis_get.return_value = None
        with (
            patch.object(crawler, "PORTAL_JSESSIONID", ""),
            patch.object(Worker, "_send_session_expired_alert") as alert,
            patch.object(Worker, "get_latest_saved_post") as latest,
        ):
            Worker.fetch_and_save_from_the_latest(32)

        alert.assert_called_once_with()
        latest.assert_not_called()


class PortalAnchorTest(SimpleTestCase):
    def setUp(self):
        self.article = Article(
            id=456, url="https://portal.kaist.ac.kr/kaist/portal/board/ntc/0#123"
        )
        articles_patch = patch.object(Article.objects, "filter")
        self.articles = articles_patch.start()
        self.addCleanup(articles_patch.stop)
        self.article_query = self.articles.return_value.order_by.return_value
        self.article_query.first.return_value = self.article

        posts_patch = patch.object(Post.objects, "filter")
        self.posts = posts_patch.start()
        self.addCleanup(posts_patch.stop)
        self.posts.return_value.first.return_value = None

    def test_anchors_to_latest_published_article_instead_of_tracking_insert_time(self):
        linked = Post(id=123, ara_article_id=self.article.id)
        self.posts.return_value.first.return_value = linked
        with patch.object(Post.objects, "latest") as tracking_latest:
            self.assertIs(Worker.get_latest_saved_post(), linked)

        self.articles.assert_called_once_with(parent_board__slug="portal-notice")
        self.articles.return_value.order_by.assert_called_once_with(
            "-created_at", "-id"
        )
        self.posts.assert_called_once_with(ara_article_id=self.article.id)
        tracking_latest.assert_not_called()

    def test_rebuilds_unlinked_article_tracking_without_creating_an_article(self):
        fresh = Post(id=123)
        with (
            patch.object(Crawler, "get_post", return_value=fresh) as get_post,
            patch.object(
                Post.objects, "update_or_create", return_value=(fresh, True)
            ) as save,
            patch.object(Article.objects, "create") as create_article,
            patch.object(Crawler, "_get_recent_post_id") as portal_latest,
        ):
            self.assertIs(Worker.get_latest_saved_post(), fresh)

        get_post.assert_called_once_with(123)
        self.assertEqual(save.call_args.kwargs["id"], 123)
        defaults = save.call_args.kwargs["defaults"]
        self.assertEqual(defaults["ara_article_id"], self.article.id)
        self.assertNotIn("created_at", defaults)
        create_article.assert_not_called()
        portal_latest.assert_not_called()

    def test_supports_legacy_portal_links(self):
        self.article.url = (
            "https://portal.kaist.ac.kr/board/read.brd?boardId=today_notice&bltnNo=123"
        )
        fresh = Post(id=123)
        with (
            patch.object(Crawler, "get_post", return_value=fresh) as get_post,
            patch.object(Post.objects, "update_or_create", return_value=(fresh, True)),
        ):
            Worker.get_latest_saved_post()
        get_post.assert_called_once_with(123)

    def test_invalid_latest_article_link_does_not_skip_unpublished_posts(self):
        for url in (
            None,
            "https://portal.kaist.ac.kr/",
            "https://portal.kaist.ac.kr/#invalid",
        ):
            with self.subTest(url=url):
                self.article.url = url
                with (
                    patch.object(Crawler, "get_post") as get_post,
                    patch.object(Crawler, "_get_recent_post_id") as portal_latest,
                    self.assertRaisesMessage(ValueError, "no valid portal post ID"),
                ):
                    Worker.get_latest_saved_post()
                get_post.assert_not_called()
                portal_latest.assert_not_called()

    def test_without_published_articles_uses_original_post_date(self):
        self.article_query.first.return_value = None
        post = Post(id=123)
        with patch.object(Post.objects, "latest", return_value=post) as latest:
            self.assertIs(Worker.get_latest_saved_post(), post)
        latest.assert_called_once_with("registered_at")
