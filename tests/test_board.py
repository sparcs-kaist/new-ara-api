import pytest
from rest_framework import status

from apps.core.models import Board
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client")
class TestBoard(TestCase, RequestSetting):
    def test_list(self):
        Board.objects.create(
            ko_name="자유 게시판",
            en_name="Free Board",
        )

        boards = self.http_request(self.user, "get", "boards")

        assert boards.status_code == status.HTTP_200_OK
        assert len(boards.data) == 1

        (board,) = boards.data

        assert board.get("en_name") == "Free Board"
