import pytest
from django.test import TestCase

from tests.conftest import RequestSetting


@pytest.mark.usefixtures('set_user_client')
class TestUserNickname(TestCase, RequestSetting):
    def test_nickname_update(self):
        # 닉네임 변경시 nickname_updated_at 변경
        update_data = {
            'see_sexual': False, 'see_social': False, 'extra_preferences': '{"test": 1}',
            'nickname': 'foo'
        }
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        self.user.refresh_from_db()

        # 오류 발생
        update_data['nickname'] = 'bar'
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data, **{'HTTP_ACCEPT_LANGUAGE': 'ko'})
        assert r.data['nickname'][0].startswith('닉네임은 3개월마다 변경할 수 있습니다.')

        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data, **{'HTTP_ACCEPT_LANGUAGE': 'en'})
        assert r.data['nickname'][0].startswith('Nicknames can only be changed every 3 months.')
