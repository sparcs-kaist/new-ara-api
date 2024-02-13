"""
 Python 3.5 이후로는 pytest-django를 쓸 때 module-scope fixture에서 DB접근이 안되기 때문에 class-scope fixture 사용
 https://github.com/pytest-dev/pytest-django/issues/53#issuecomment-407073682
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase as DjangoTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import Article, Board, Topic, UserProfile
from apps.core.models.board import NameType
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
    client.force_authenticate(user=request.cls.admin)
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
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
            group=UserProfile.UserGroup.KAIST_MEMBER,
            agree_terms_of_service_at=timezone.now(),
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
            group=UserProfile.UserGroup.COMMUNICATION_BOARD_ADMIN,
            sso_user_info={
                "kaist_info": '{"ku_kname": "\\ud669"}',
                "first_name": "FirstName",
                "last_name": "LastName",
            },
        )

    request.cls.api_client = APIClient()


@pytest.fixture(scope="class")
def set_boards(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
        name_type=NameType.REGULAR,
    )

    request.cls.anon_board = Board.objects.create(
        slug="anonymous",
        ko_name="익명 게시판",
        en_name="Anonymous",
        name_type=NameType.ANONYMOUS,
    )

    request.cls.free_board = Board.objects.create(
        slug="free",
        ko_name="자유 게시판",
        en_name="Free",
        name_type=NameType.ANONYMOUS | NameType.REGULAR,
    )

    request.cls.realname_board = Board.objects.create(
        slug="test realname board",
        ko_name="테스트 실명 게시판",
        en_name="Test realname Board",
        name_type=NameType.REALNAME,
    )

    request.cls.regular_access_board = Board.objects.create(
        slug="regular access",
        ko_name="일반 접근 권한 게시판",
        en_name="Regular Access Board",
        read_access_mask=0b11011110,
        write_access_mask=0b11011010,
    )

    # Though its name is 'advertiser accessible', enterprise is also accessible
    request.cls.advertiser_accessible_board = Board.objects.create(
        slug="advertiser accessible",
        ko_name="외부인(홍보 계정) 접근 가능 게시판",
        en_name="Advertiser Accessible Board",
        read_access_mask=0b11111110,
        write_access_mask=0b11111110,
    )

    request.cls.nonwritable_board = Board.objects.create(
        slug="nonwritable",
        ko_name="글 작성 불가 게시판",
        en_name="Nonwritable Board",
        write_access_mask=0b00000000,
    )

    request.cls.newsadmin_writable_board = Board.objects.create(
        slug="newsadmin writable",
        ko_name="뉴스게시판 관리인 글 작성 가능 게시판",
        en_name="Newsadmin Writable Board",
        write_access_mask=0b10000000,
    )

    request.cls.enterprise_writable_board = Board.objects.create(
        slug="enterprise writable",
        ko_name="입주업체 글 작성 가능 게시판",
        en_name="Enterprise Writable Board",
        write_access_mask=0b11011110,
    )


@pytest.fixture(scope="class")
def set_topics(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug="test topic",
        ko_name="테스트 토픽",
        en_name="Test Topic",
        parent_board=request.cls.board,
    )

    request.cls.realname_topic = Topic.objects.create(
        slug="test realname topic",
        ko_name="테스트 실명 토픽",
        en_name="Test realname Topic",
        parent_board=request.cls.realname_board,
    )


@pytest.fixture(scope="class")
def set_articles(request):
    """set_board 먼저 적용"""
    request.cls.article = Article.objects.create(
        title="example article",
        content="example content",
        content_text="example content text",
        name_type=NameType.REGULAR,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now(),
    )

    request.cls.regular_access_article = Article.objects.create(
        title="regular access article",
        content="regular access article content",
        content_text="regular access article content",
        created_by=request.cls.user,
        parent_board=request.cls.regular_access_board,
    )

    request.cls.advertiser_accessible_article = Article.objects.create(
        title="advertiser readable article",
        content="advertiser readable article content",
        content_text="advertiser readable article content",
        created_by=request.cls.user,
        parent_board=request.cls.advertiser_accessible_board,
    )


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
        group: UserProfile.UserGroup = UserProfile.UserGroup.KAIST_MEMBER,
    ) -> User:
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            UserProfile.objects.create(
                user=user,
                nickname=nickname,
                group=group,
                agree_terms_of_service_at=timezone.now(),
                sso_user_info={
                    "kaist_info": '{"ku_kname": "\\ud669"}',
                    "first_name": f"Firstname",
                    "last_name": f"Lastname",
                },
            )
        return user

    @classmethod
    def create_user_with_index(cls, idx: int, group: UserProfile.UserGroup) -> User:
        user = cls.create_user(
            username=f"User{idx}",
            email=f"user{idx}@sparcs.org",
            nickname=f"Nickname{idx}",
            group=group,
        )
        return user

    @classmethod
    def create_users(
        cls,
        num: int,
        group: UserProfile.UserGroup = UserProfile.UserGroup.KAIST_MEMBER,
    ) -> list[User]:
        return [cls.create_user_with_index(idx, group) for idx in range(num)]
