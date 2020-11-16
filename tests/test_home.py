import pytest
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures('set_user_client')
class TestHome(TestCase, RequestSetting):
    def test_board_perm(self):
        r = self.http_request(self.user, 'get', 'home')
        assert r.status_code == 200

        r = self.http_request(None, 'get', 'home')
        assert r.status_code == 401
