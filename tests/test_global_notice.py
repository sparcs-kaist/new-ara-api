import pytest
from django.utils import timezone
from rest_framework import status

from apps.global_notice.models import GlobalNotice
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_admin_client", "set_user_client")
class TestGlobalNotice(TestCase, RequestSetting):
    N = 50

    def test_list(self):
        """
        비로그인도 허용
        """
        for i in range(self.N):
            GlobalNotice.objects.create(
                title=f"global_notice title {i}",
                content=f"global_notice content {i}",
                started_at=timezone.now() - timezone.timedelta(days=1),
                expired_at=timezone.now() + timezone.timedelta(days=1),
            )
        res = self.http_request(self.user, "get", "global_notices")
        assert len(res.data) == self.N

        res = self.http_request(None, "get", "global_notices")
        assert len(res.data) == self.N

    def test_get(self):
        """
        비로그인도 허용
        """
        global_notice = GlobalNotice.objects.create(
            title=f"global_notice title",
            content=f"global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=1),
        )
        res = self.http_request(self.user, "get", f"global_notices/{global_notice.id}")
        assert res.data["title"] == global_notice.title

        res = self.http_request(None, "get", f"global_notices/{global_notice.id}")
        assert res.data["title"] == global_notice.title

    def test_filter(self):
        """
        expired, not started 필터링 테스트
        """
        global_notice_expired = GlobalNotice.objects.create(
            title="global_notice title",
            content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=2),
            expired_at=timezone.now() - timezone.timedelta(days=1),
        )
        global_notice_not_started = GlobalNotice.objects.create(
            title="global_notice title",
            content="global_notice content",
            started_at=timezone.now() + timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=2),
        )

        res = self.http_request(
            self.user, "get", f"global_notices/{global_notice_expired.id}"
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        res = self.http_request(
            self.user, "get", f"global_notices/{global_notice_not_started.id}"
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_create(self):
        notice_data = {
            "title": "global_notice title",
            "content": "global_notice content",
            "started_at": timezone.now() - timezone.timedelta(days=1),
            "expired_at": timezone.now() + timezone.timedelta(days=1),
        }
        res_user = self.http_request(self.user, "post", "global_notices", notice_data)
        assert res_user.status_code == status.HTTP_403_FORBIDDEN

        for _ in range(self.N):
            res_admin = self.http_request(
                self.admin, "post", "global_notices", notice_data
            )
            assert res_admin.status_code == status.HTTP_201_CREATED

        assert GlobalNotice.objects.count() == self.N

    def test_update(self):
        global_notice = GlobalNotice.objects.create(
            title="global_notice title",
            content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=1),
        )
        new_title = "new title"
        new_content = "new content"

        res_user = self.http_request(
            self.user,
            "patch",
            f"global_notices/{global_notice.id}",
            {"title": new_title, "content": new_content},
        )
        assert res_user.status_code == status.HTTP_403_FORBIDDEN

        res_admin = self.http_request(
            self.admin,
            "patch",
            f"global_notices/{global_notice.id}",
            {"title": new_title, "content": new_content},
        )
        assert res_admin.status_code == status.HTTP_200_OK
        assert res_admin.data["title"] == new_title
        assert res_admin.data["content"] == new_content

    def test_destroy(self):
        global_notice = GlobalNotice.objects.create(
            title="global_notice title",
            content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=1),
        )
        res_user = self.http_request(
            self.user,
            "delete",
            f"global_notices/{global_notice.id}",
        )
        assert res_user.status_code == status.HTTP_403_FORBIDDEN

        res_admin = self.http_request(
            self.admin,
            "delete",
            f"global_notices/{global_notice.id}",
        )
        assert res_admin.status_code == status.HTTP_204_NO_CONTENT
        assert GlobalNotice.objects.count() == 0
