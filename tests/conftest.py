"""
 Python 3.5 이후로는 pytest-django를 쓸 때 module-scope fixture에서 DB접근이 안되기 때문에 class-scope fixture 사용
 https://github.com/pytest-dev/pytest-django/issues/53#issuecomment-407073682
"""

import pytest
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.user.models import UserProfile
from ara import redis


@pytest.fixture(scope='class')
def set_admin_client(request):
    request.cls.admin, _ = User.objects.get_or_create(username='관리자', email='admin@sparcs.org', is_superuser=True)
    if not hasattr(request.cls.admin, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.admin, nickname='관리자', agree_terms_of_service_at=timezone.now())
    client = APIClient()
    client.force_authenticate(user=request.cls.user)
    request.cls.api_client = client


@pytest.fixture(scope='class')
def set_user_client(request):
    request.cls.user, _ = User.objects.get_or_create(username='User', email='user@sparcs.org')
    if not hasattr(request.cls.user, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.user, nickname='User',
                                          group=UserProfile.UserGroup.KAIST_MEMBER, agree_terms_of_service_at=timezone.now())
    client = APIClient()
    request.cls.api_client = client


@pytest.fixture(scope='class')
def set_user_client2(request):
    request.cls.user2, _ = User.objects.get_or_create(username='User2', email='user2@sparcs.org')
    if not hasattr(request.cls.user2, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.user2, nickname='User2',
                                          group=UserProfile.UserGroup.KAIST_MEMBER, agree_terms_of_service_at=timezone.now())
    request.cls.api_client = APIClient()


@pytest.fixture(scope='class')
def set_user_client3(request):
    request.cls.user3, _ = User.objects.get_or_create(username='User3', email='user3@sparcs.org')
    if not hasattr(request.cls.user3, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.user3, nickname='User3',
                                          group=UserProfile.UserGroup.KAIST_MEMBER, agree_terms_of_service_at=timezone.now())

    request.cls.api_client = APIClient()

@pytest.fixture(scope='class')
def set_user_client4(request):
    request.cls.user4, _ = User.objects.get_or_create(username='User4', email='user4@sparcs.org')
    if not hasattr(request.cls.user4, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.user4, nickname='User4',
                                          group=UserProfile.UserGroup.KAIST_MEMBER, agree_terms_of_service_at=timezone.now())

    request.cls.api_client = APIClient()


class RequestSetting:
    def http_request(self, user, method, path, data=None, querystring='', **kwargs):
        self.api_client.force_authenticate(user=user)

        request_func = {
            'post': self.api_client.post,
            'patch': self.api_client.patch,
            'put': self.api_client.put,
            'get': self.api_client.get,
            'delete': self.api_client.delete
        }
        url = f'/api/{path}/?{querystring}'
        return request_func[method](url, data=data, format='json', **kwargs)


class TestCase(DjangoTestCase):
    @classmethod
    def setUpClass(cls):
        redis.flushall()
        super().setUpClass()

    def tearDown(self):
        redis.flushall()
        super().tearDown()
