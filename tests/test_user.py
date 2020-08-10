from datetime import timedelta

import pytest
from django.test import TestCase
from django.utils import timezone
from tests.conftest import RequestSetting


@pytest.mark.usefixtures('set_user_client_with_profile')
class TestUserNickname(TestCase, RequestSetting):
    def test_nickname_update(self):
        # 사용자가 처음 생성됨 -> 변경된 적이 없으므로 None
        assert self.user.profile.nickname_updated_at is None

        # 닉네임 변경시 nickname_updated_at 변경
        update_data = {
            'see_sexual': False, 'see_social': False, 'extra_preferences': '{"test": 1}',
            'nickname': 'foo'
        }
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert r.status_code == 200
        self.user.refresh_from_db()
        assert self.user.profile.nickname == 'foo'
        assert (timezone.now() - self.user.profile.nickname_updated_at).total_seconds() < 5

        # 닉네임이 현재 닉네임과 동일하다면 오류가 발생하지 않음
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert r.status_code == 200

        # 닉네임이 다르다면 오류 발생
        update_data['nickname'] = 'bar'
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert r.status_code != 200

        # 3개월이 좀 안됐을 경우 오류 발생
        self.user.profile.nickname_updated_at -= timedelta(days=60)
        self.user.profile.save()
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert r.status_code != 200

        # 3개월 이전일 경우 정상적으로 변경
        self.user.profile.nickname_updated_at -= timedelta(days=31)
        self.user.profile.save()
        r = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert r.status_code == 200
        self.user.refresh_from_db()
        assert self.user.profile.nickname == 'bar'
        assert (timezone.now() - self.user.profile.nickname_updated_at).total_seconds() < 5
