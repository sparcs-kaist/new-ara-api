"""
 Python 3.5 이후로는 pytest-django를 쓸 때 module-scope fixture에서 DB접근이 안되기 때문에 class-scope fixture 사용
 https://github.com/pytest-dev/pytest-django/issues/53#issuecomment-407073682
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase as DjangoTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.user.models import Group, UserGroup, UserProfile
from ara import redis

User = get_user_model()


@pytest.fixture(scope="class")
def set_admin_client(request):
    request.cls.admin, _ = User.objects.get_or_create(
        username="관리자", email="admin@sparcs.org", is_superuser=True
    )
    if not hasattr(request.cls.admin, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.admin,
            nickname="관리자",
            agree_terms_of_service_at=timezone.now(),
        )
    client = APIClient()
    client.force_authenticate(user=request.cls.user)
    request.cls.api_client = client


@pytest.fixture(scope="class")
def set_user_client(request):
    request.cls.user, _ = User.objects.get_or_create(
        username="User",
        email="user@sparcs.org",
    )
    if not hasattr(request.cls.user, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user,
            nickname="User",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )
        UserGroup.objects.create(
            user=request.cls.user,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )
    client = APIClient()
    request.cls.api_client = client


@pytest.fixture(scope="class")
def set_user_client2(request):
    request.cls.user2, _ = User.objects.get_or_create(
        username="User2", email="user2@sparcs.org"
    )
    if not hasattr(request.cls.user2, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user2,
            nickname="User2",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )
        UserGroup.objects.create(
            user=request.cls.user2,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )
    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_user_client3(request):
    request.cls.user3, _ = User.objects.get_or_create(
        username="User3", email="user3@sparcs.org"
    )
    if not hasattr(request.cls.user3, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user3,
            nickname="User3",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )
        UserGroup.objects.create(
            user=request.cls.user3,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )

    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_user_client4(request):
    request.cls.user4, _ = User.objects.get_or_create(
        username="User4", email="user4@sparcs.org"
    )
    if not hasattr(request.cls.user4, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user4,
            nickname="User4",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )
        UserGroup.objects.create(
            user=request.cls.user4,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )

    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_user_with_kaist_info(request):
    request.cls.user_with_kaist_info, _ = User.objects.get_or_create(
        username="User_with_kaist_info", email="user_with_kaist_info@sparcs.org"
    )
    if not hasattr(request.cls.user_with_kaist_info, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user_with_kaist_info,
            nickname="user_with_kinfo",
            sso_user_info={"kaist_info": '{"ku_kname": "user_with_kaist_info"}'},
            agree_terms_of_service_at=timezone.now(),
        )
        UserGroup.objects.create(
            user=request.cls.user_with_kaist_info,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )

    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_user_without_kaist_info(request):
    request.cls.user_without_kaist_info, _ = User.objects.get_or_create(
        username="User_without_kaist_info", email="user_without_kaist_info@sparcs.org"
    )
    if not hasattr(request.cls.user_without_kaist_info, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.user_without_kaist_info,
            nickname="user_without_kinfo",
            sso_user_info={
                "kaist_info": None,
                "last_name": "user_",
                "first_name": "without_kaist_info",
            },
            agree_terms_of_service_at=timezone.now(),
        )
        UserGroup.objects.create(
            user=request.cls.user_without_kaist_info,
            group=Group.search_by_id(2),  # 2 = KAIST_MEMBER
        )

    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_school_admin(request):
    request.cls.school_admin, _ = User.objects.get_or_create(
        username="School Admin", email="schooladmin@sparcs.org"
    )
    if not hasattr(request.cls.school_admin, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.school_admin,
            nickname="School Admin",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )
        UserGroup.objects.create(
            user=request.cls.school_admin,
            group=Group.search_by_id(7),  # 7 = Communication board admin
        )

    request.cls.api_client = APIClient()


class RequestSetting:
    def http_request(self, user, method, path, data=None, querystring="", **kwargs):
        self.api_client.force_authenticate(user=user)

        request_func = {
            "post": self.api_client.post,
            "patch": self.api_client.patch,
            "put": self.api_client.put,
            "get": self.api_client.get,
            "delete": self.api_client.delete,
        }
        url = f"/api/{path}/?{querystring}"
        return request_func[method](url, data=data, format="json", **kwargs)


class TestCase(DjangoTestCase):
    @classmethod
    def setUpClass(cls):
        redis.flushall()
        super().setUpClass()

    def tearDown(self):
        redis.flushall()
        super().tearDown()


class Utils:
    @staticmethod
    def create_user(
        username: str = "User",
        email: str = "user@sparcs.org",
        nickname: str = "Nickname",
        group: Group = Group.search_by_id(2),  # 2 = KAIST_MEMBER
    ) -> User:
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            UserProfile.objects.create(
                user=user,
                nickname=nickname,
                agree_terms_of_service_at=timezone.now(),
                sso_user_info={
                    "kaist_info": '{"ku_kname": "\\ud669"}',
                    "first_name": f"Firstname",
                    "last_name": f"Lastname",
                },
            )
            UserGroup.objects.create(user=user, group=group)
        return user

    @classmethod
    def create_user_with_index(cls, idx: int, group: Group) -> User:
        user = cls.create_user(
            username=f"User{idx}",
            email=f"user{idx}@sparcs.org",
            nickname=f"Nickname{idx}",
        )
        UserGroup.objects.create(user=user, group=group)
        return user

    @classmethod
    def create_users(
        cls,
        num: int,
        group: Group = Group.search_by_id(2),  # 2 = KAIST_MEMBER
    ) -> list[User]:
        return [cls.create_user_with_index(idx, group) for idx in range(num)]

    @classmethod
    def add_default_groups(cls):
        default_groups = {
            1: ("Unauthorized user", "뉴아라 계정을 만들지 않은 사람들", False),
            2: ("KAIST member", "카이스트 메일을 가진 사람 (학생, 교직원)", False),
            3: ("Store employee", "교내 입주 업체 직원", False),
            4: ("Other member", "카이스트 메일이 없는 개인 (특수한 관련자 등)", False),
            5: ("KAIST organization", "교내 학생 단체들", True),
            6: ("External organization", "외부인 (홍보 계정 등)", True),
            7: ("Communication board admin", "소통게시판 관리인", False),
            8: ("News board admin", "뉴스게시판 관리인", False),
        }

        for group_id, (name, description, is_official) in default_groups.items():
            Group.objects.create(
                group_id=group_id,
                name=name,
                description=description,
                is_official=is_official,
            )
