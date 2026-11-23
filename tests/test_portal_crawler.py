from unittest.mock import patch

import requests
from django.test import SimpleTestCase

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
            patch.object(Post.objects, "latest", return_value=post),
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
            patch.object(Post.objects, "latest") as latest,
        ):
            Worker.fetch_and_save_from_the_latest(32)

        alert.assert_called_once_with()
        latest.assert_not_called()
