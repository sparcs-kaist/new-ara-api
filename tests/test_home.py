import pytest
from rest_framework import status

from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client")
class TestHome(TestCase, RequestSetting):
    def test_board_permission(self):
        res = self.http_request(self.user, "get", "home")
        assert res.status_code == status.HTTP_200_OK

        res = self.http_request(None, "get", "home")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
