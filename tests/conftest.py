"""
 Python 3.5 이후로는 pytest-django를 쓸 때 module-scope fixture에서 DB접근이 안되기 때문에 class-scope fixture 사용
 https://github.com/pytest-dev/pytest-django/issues/53#issuecomment-407073682
"""

import pytest
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from rest_framework.test import APIClient

from apps.user.models import UserProfile


@pytest.fixture(scope='class')
def set_admin_client(request):
    request.cls.user, _ = User.objects.get_or_create(username='관리자', email='admin@sparcs.org', is_superuser=True)
    client = APIClient()
    client.force_authenticate(user=request.cls.user)
    request.cls.api_client = client


@pytest.fixture(scope='class')
def set_user_client(request):
    request.cls.user, _ = User.objects.get_or_create(username='User', email='user@sparcs.org')
    client = APIClient()
    request.cls.api_client = client


@pytest.fixture(scope='function')
def set_user_client2(request):
    request.cls.user2, _ = User.objects.get_or_create(username='User2', email='user2@sparcs.org')
    client = APIClient()
    request.cls.api_client = client


class RequestSetting:
    def http_request(self, user, method, path, data=None, querystring=''):
        self.user = user
        self.api_client.force_authenticate(user=self.user)

        request_func = {
            'post': self.api_client.post,
            'patch': self.api_client.patch,
            'put': self.api_client.put,
            'get': self.api_client.get,
            'delete': self.api_client.delete
        }
        url = f'/api/{path}/?{querystring}'
        return request_func[method](url, data, format='json')


@pytest.fixture(scope='class')
def set_user_client_with_profile(request):
    request.cls.user, _ = User.objects.get_or_create(username='User', email='user@sparcs.org')
    if not hasattr(request.cls.user, 'profile'):
        user_profile = UserProfile(user=request.cls.user, nickname='TestUser')
        user_profile.save()
    client = APIClient()
    request.cls.api_client = client


class TestCase(DjangoTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def tearDown(self):
        super().tearDown()
