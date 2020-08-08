import pytest
from django.test import TestCase

from apps.core.models import Board
from tests.conftest import RequestSetting


@pytest.mark.usefixtures('set_user_client')
class TestBoard(TestCase, RequestSetting):

    def test_list(self):
        Board.objects.create(ko_name='자유 게시판',
                             en_name='Free Board',
                             ko_description='자유 게시판 입니다.',
                             en_description='This is a free board.')

        boards = self.http_request(self.user, 'get', 'boards')

        assert boards.data.get('num_items') == 1
        assert boards.data.get('results')[0].get('en_name') == 'Free Board'
