import pytest

from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client")
class TestInternationalization(TestCase, RequestSetting):
    def test_nickname_update(self):
        # 닉네임 변경시 nickname_updated_at 변경
        update_data = {
            "see_sexual": False,
            "see_social": False,
            "nickname": "foo",
        }
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        self.user.refresh_from_db()

        update_data["nickname"] = "bar"
        r = self.http_request(
            self.user,
            "put",
            f"user_profiles/{self.user.id}",
            data=update_data,
            **{"HTTP_ACCEPT_LANGUAGE": "ko"},
        )
        assert r.data["nickname"][0].startswith("닉네임은 3개월마다 변경할 수 있습니다.")

        r = self.http_request(
            self.user,
            "put",
            f"user_profiles/{self.user.id}",
            data=update_data,
            **{"HTTP_ACCEPT_LANGUAGE": "en"},
        )
        assert r.data["nickname"][0].startswith(
            "Nicknames can only be changed every 3 months."
        )
