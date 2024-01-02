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
                ko_title=f"글로벌 공지 제목 {i}",
                en_title=f"global_notice title {i}",
                ko_content=f"글로벌 공지 본문 {i}",
                en_content=f"global_notice content {i}",
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
            ko_title="글로벌 공지 제목",
            en_title="global_notice title",
            ko_content="글로벌 공지 본문",
            en_content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=1),
        )
        res = self.http_request(self.user, "get", f"global_notices/{global_notice.id}")
        assert res.data["ko_title"] == global_notice.ko_title
        assert res.data["en_title"] == global_notice.en_title

        res = self.http_request(None, "get", f"global_notices/{global_notice.id}")
        assert res.data["ko_title"] == global_notice.ko_title
        assert res.data["en_title"] == global_notice.en_title

    def test_filter(self):
        """
        expired, not started 필터링 테스트
        """
        global_notice_expired = GlobalNotice.objects.create(
            ko_title="글로벌 공지 제목",
            en_title="global_notice title",
            ko_content="글로벌 공지 본문",
            en_content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=2),
            expired_at=timezone.now() - timezone.timedelta(days=1),
        )
        global_notice_not_started = GlobalNotice.objects.create(
            ko_title="글로벌 공지 제목",
            en_title="global_notice title",
            ko_content="글로벌 공지 본문",
            en_content="global_notice content",
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
            "ko_title": "글로벌 공지 제목",
            "en_title": "global_notice title",
            "ko_content": "글로벌 공지 본문",
            "en_content": "global_notice content",
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
            ko_title="글로벌 공지 제목",
            en_title="global_notice title",
            ko_content="글로벌 공지 본문",
            en_content="global_notice content",
            started_at=timezone.now() - timezone.timedelta(days=1),
            expired_at=timezone.now() + timezone.timedelta(days=1),
        )
        new_ko_title = "새로운 제목"
        new_ko_content = "새로운 본문"

        res_user = self.http_request(
            self.user,
            "patch",
            f"global_notices/{global_notice.id}",
            {"ko_title": new_ko_title, "ko_content": new_ko_content},
        )
        assert res_user.status_code == status.HTTP_403_FORBIDDEN

        res_admin = self.http_request(
            self.admin,
            "patch",
            f"global_notices/{global_notice.id}",
            {"ko_title": new_ko_title, "ko_content": new_ko_content},
        )
        assert res_admin.status_code == status.HTTP_200_OK
        assert res_admin.data["ko_title"] == new_ko_title
        assert res_admin.data["ko_content"] == new_ko_content

    def test_destroy(self):
        global_notice = GlobalNotice.objects.create(
            ko_title="글로벌 공지 제목",
            en_title="global_notice title",
            ko_content="글로벌 공지 본문",
            en_content="global_notice content",
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
