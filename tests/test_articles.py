import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status

from apps.core.models import Article, Block, Board, Comment, Topic, Vote
from apps.core.models.board import NameType
from apps.core.models.board_permission import (
    DEFAULT_COMMENT_PERMISSION,
    DEFAULT_READ_PERMISSION,
    DEFAULT_WRITE_PERMISSION,
    BoardAccessPermissionType,
    BoardPermission,
)
from apps.user.models import Group, UserGroup, UserProfile
from ara.settings import MIN_TIME, SCHOOL_RESPONSE_VOTE_THRESHOLD
from tests.conftest import RequestSetting, TestCase, Utils


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
        # read_access_mask=0b11011110,
        # write_access_mask=0b11011010,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = [
        (2, BoardAccessPermissionType.READ),
        (3, BoardAccessPermissionType.READ),
        (4, BoardAccessPermissionType.READ),
        (5, BoardAccessPermissionType.READ),
        (7, BoardAccessPermissionType.READ),
        (8, BoardAccessPermissionType.READ),
        (2, BoardAccessPermissionType.WRITE),
        (4, BoardAccessPermissionType.WRITE),
        (5, BoardAccessPermissionType.WRITE),
        (7, BoardAccessPermissionType.WRITE),
        (8, BoardAccessPermissionType.WRITE),
    ]
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.regular_access_board, permission_bulk
    )

    # Though its name is 'advertiser accessible', enterprise is also accessible
    request.cls.advertiser_accessible_board = Board.objects.create(
        slug="advertiser accessible",
        ko_name="외부인(홍보 계정) 접근 가능 게시판",
        en_name="Advertiser Accessible Board",
        # read_access_mask=0b11111110,
        # write_access_mask=0b11111110,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = [
        (2, BoardAccessPermissionType.READ),
        (3, BoardAccessPermissionType.READ),
        (4, BoardAccessPermissionType.READ),
        (5, BoardAccessPermissionType.READ),
        (7, BoardAccessPermissionType.READ),
        (8, BoardAccessPermissionType.READ),
        (2, BoardAccessPermissionType.WRITE),
        (4, BoardAccessPermissionType.WRITE),
        (5, BoardAccessPermissionType.WRITE),
        (6, BoardAccessPermissionType.WRITE),
        (7, BoardAccessPermissionType.WRITE),
        (8, BoardAccessPermissionType.WRITE),
    ]
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.advertiser_accessible_board, permission_bulk
    )

    request.cls.nonwritable_board = Board.objects.create(
        slug="nonwritable",
        ko_name="글 작성 불가 게시판",
        en_name="Nonwritable Board",
        # write_access_mask=0b00000000,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = []
    permission_bulk.extend(DEFAULT_READ_PERMISSION)
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.nonwritable_board, permission_bulk
    )

    request.cls.newsadmin_writable_board = Board.objects.create(
        slug="newsadmin writable",
        ko_name="뉴스게시판 관리인 글 작성 가능 게시판",
        en_name="Newsadmin Writable Board",
        # write_access_mask=0b10000000,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = [
        (8, BoardAccessPermissionType.WRITE),
    ]
    permission_bulk.extend(DEFAULT_READ_PERMISSION)
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.newsadmin_writable_board, permission_bulk
    )

    request.cls.enterprise_writable_board = Board.objects.create(
        slug="enterprise writable",
        ko_name="입주업체 글 작성 가능 게시판",
        en_name="Enterprise Writable Board",
        # write_access_mask=0b11011110,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = [
        (2, BoardAccessPermissionType.WRITE),
        (3, BoardAccessPermissionType.WRITE),
        (4, BoardAccessPermissionType.WRITE),
        (5, BoardAccessPermissionType.WRITE),
        (7, BoardAccessPermissionType.WRITE),
        (8, BoardAccessPermissionType.WRITE),
    ]
    permission_bulk.extend(DEFAULT_READ_PERMISSION)
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.enterprise_writable_board, permission_bulk
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


@pytest.fixture(scope="class")
def set_realname_article(request):
    """set_user_with_kaist_info,, set_realname_topic, set_realname_board 먼저 적용"""
    request.cls.realname_article = Article.objects.create(
        title="Realname Test Article",
        content="Content of test realname article",
        content_text="Content of test article in text",
        name_type=NameType.REALNAME,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user_with_kaist_info,
        parent_topic=request.cls.realname_topic,
        parent_board=request.cls.realname_board,
        commented_at=timezone.now(),
    )


@pytest.fixture(scope="function")
def set_kaist_articles(request):
    request.cls.non_kaist_user, _ = User.objects.get_or_create(
        username="NonKaistUser", email="non-kaist-user@sparcs.org"
    )
    if not hasattr(request.cls.non_kaist_user, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.non_kaist_user,
            nickname="Not a KAIST User",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={},
        )
    request.cls.kaist_user, _ = User.objects.get_or_create(
        username="KaistUser", email="kaist-user@sparcs.org"
    )
    if not hasattr(request.cls.kaist_user, "profile"):
        UserProfile.objects.get_or_create(
            user=request.cls.kaist_user,
            nickname="KAIST User",
            agree_terms_of_service_at=timezone.now(),
            sso_user_info={},
        )
        UserGroup.objects.get_or_create(
            user=request.cls.kaist_user,
            group=Group.search_by_id(2),  # 2 = KAIST member
        )

    request.cls.kaist_board, _ = Board.objects.get_or_create(
        slug="kaist-only",
        ko_name="KAIST Board",
        en_name="KAIST Board",
        # read_access_mask=0b00000010,
        # write_access_mask=0b00000010,
    )
    permission_bulk: list[tuple[int, BoardAccessPermissionType]] = [
        (2, BoardAccessPermissionType.READ),
        (2, BoardAccessPermissionType.WRITE),
    ]
    permission_bulk.extend(DEFAULT_COMMENT_PERMISSION)
    BoardPermission.add_permission_bulk_by_board(
        request.cls.kaist_board, permission_bulk
    )

    request.cls.kaist_article, _ = Article.objects.get_or_create(
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
        parent_board=request.cls.kaist_board,
        commented_at=timezone.now(),
    )
    yield None
    request.cls.kaist_board.delete()
    request.cls.kaist_article.delete()


@pytest.fixture(scope="function")
def set_readonly_board(request):
    request.cls.readonly_board, _ = Board.objects.get_or_create(
        slug="readonly",
        ko_name="읽기전용 게시판",
        en_name="Read Only Board",
        is_readonly=True,
    )
    yield None
    request.cls.readonly_board.delete()


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_client3",
    "set_user_client4",
    "set_user_with_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
)
class TestArticle(TestCase, RequestSetting):
    def test_list(self):
        # article 개수를 확인하는 테스트
        res = self.http_request(self.user, "get", "articles")
        assert res.data.get("num_items") == Article.objects.count()

        Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            name_type=NameType.REGULAR,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now(),
        )

        Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            name_type=NameType.REGULAR,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now(),
        )

        res = self.http_request(self.user, "get", "articles")
        assert res.data.get("num_items") == Article.objects.count()

    def test_get(self):
        # article 조회가 잘 되는지 확인
        res = self.http_request(self.user, "get", f"articles/{self.article.id}").data
        assert res.get("title") == self.article.title
        assert res.get("content") == self.article.content
        assert res.get("name_type") == self.article.name_type
        assert res.get("is_content_sexual") == self.article.is_content_sexual
        assert res.get("is_content_social") == self.article.is_content_social
        assert res.get("positive_vote_count") == self.article.positive_vote_count
        assert res.get("negative_vote_count") == self.article.negative_vote_count
        assert res.get("created_by")["username"] == self.user.username
        assert res.get("parent_topic")["ko_name"] == self.article.parent_topic.ko_name
        assert res.get("parent_board")["ko_name"] == self.article.parent_board.ko_name

    # http get으로 익명 게시글을 retrieve했을 때 작성자가 익명으로 나타나는지 확인
    def test_anonymous_article(self):
        # 익명 게시글 생성
        anon_article = Article.objects.create(
            title="example anonymous article",
            content="example anonymous content",
            content_text="example anonymous content text",
            name_type=NameType.ANONYMOUS,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=None,
            parent_board=self.anon_board,
            commented_at=timezone.now(),
        )

        # 익명 게시글을 GET할 때, 작성자의 정보가 전달되지 않는 것 확인
        res = self.http_request(self.user, "get", f"articles/{anon_article.id}").data
        assert res.get("name_type") == NameType.ANONYMOUS
        assert res.get("created_by")["username"] != anon_article.created_by.username

        res2 = self.http_request(self.user2, "get", f"articles/{anon_article.id}").data
        assert res2.get("name_type") == NameType.ANONYMOUS
        assert res2.get("created_by")["username"] != anon_article.created_by.username

    def test_create(self):
        # test_create: HTTP request (POST)를 이용해서 생성
        # user data in dict
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "name_type": NameType.REGULAR.name,
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": self.topic.id,
            "parent_board": self.board.id,
        }
        # convert user data to JSON
        self.http_request(self.user, "post", "articles", user_data)
        assert Article.objects.filter(title="article for test_create")

    # get request 시 user의 read 권한 확인 테스트
    def test_check_read_permission_when_get(self):
        group_users = []
        for group in Group.objects.all():
            user = Utils.create_user_with_index(group.group_id, group)
            group_users.append(user)

        assert len(group_users) == len(Group.objects.all())

        articles = [self.regular_access_article, self.advertiser_accessible_article]

        for user in group_users:
            for article in articles:
                res = self.http_request(user, "get", f"articles/{article.id}")

                if article.parent_board.permission_list_by_user(user).READ:
                    assert res.status_code == status.HTTP_200_OK
                    assert res.data["id"] == article.id
                else:
                    assert res.status_code == status.HTTP_403_FORBIDDEN

    # create 단계에서 user의 write 권한 확인 테스트
    def test_check_write_permission_when_create(self):
        group_users = []
        for group in Group.objects.all():
            user = Utils.create_user_with_index(group.group_id, group)
            group_users.append(user)
        assert len(group_users) == len(Group.objects.all())

        boards = [
            self.regular_access_board,
            self.nonwritable_board,
            self.newsadmin_writable_board,
            self.enterprise_writable_board,
            self.advertiser_accessible_board,
        ]

        for user in group_users:
            for board in boards:
                res = self.http_request(
                    user,
                    "post",
                    "articles",
                    {
                        "title": "title in write permission test",
                        "content": "content in write permission test",
                        "content_text": "content_text in write permission test",
                        "parent_board": board.id,
                        "name_type": NameType.REGULAR.name,
                    },
                )

                if board.permission_list_by_user(user).WRITE:
                    assert res.status_code == status.HTTP_201_CREATED
                else:
                    assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_create_regular(self):
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": self.topic.id,
            "parent_board": self.board.id,
            "name_type": NameType.REGULAR.name,
        }

        result = self.http_request(self.user, "post", "articles", user_data)

        assert result.data["name_type"] == NameType.REGULAR

    def test_create_anonymous(self):
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": None,
            "parent_board": self.anon_board.id,
            "name_type": NameType.ANONYMOUS.name,
        }

        result = self.http_request(self.user, "post", "articles", user_data)

        assert result.data["name_type"] == NameType.ANONYMOUS

    # 자유게시판에 익명, 닉네임 게시글 만들 수 있다
    def test_create_free(self):
        for name_type in [NameType.ANONYMOUS, NameType.REGULAR]:
            user_data = {
                "title": "article for test_create",
                "content": "content for test_create",
                "content_text": "content_text for test_create",
                "is_content_sexual": False,
                "is_content_social": False,
                "parent_topic": None,
                "parent_board": self.free_board.id,
                "name_type": name_type.name,
            }

            result = self.http_request(self.user, "post", "articles", user_data)
            assert result.data["name_type"] == name_type

    # 일반 게시판에 익명 게시글을 만들 수 없다
    def test_create_invalid1(self):
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": None,
            "parent_board": self.board.id,
            "name_type": NameType.ANONYMOUS.name,
        }

        result = self.http_request(self.user, "post", "articles", user_data)
        assert result.status_code == status.HTTP_400_BAD_REQUEST

    # 실명 게시판에 익명 게시글, 닉네임 게시글을 만들 수 없다
    def test_create_invalid2(self):
        for name_type in [NameType.ANONYMOUS, NameType.REGULAR]:
            user_data = {
                "title": "article for test_create",
                "content": "content for test_create",
                "content_text": "content_text for test_create",
                "is_content_sexual": False,
                "is_content_social": False,
                "parent_topic": None,
                "parent_board": self.realname_board.id,
                "name_type": name_type.name,
            }

            result = self.http_request(self.user, "post", "articles", user_data)
            assert result.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_cache_sync(self):
        new_title = "title changed!"
        new_content = "content changed!"
        article = Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            name_type=NameType.REGULAR,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now(),
        )
        # 캐시 업데이트 확인을 위해 GET을 미리 한번 함
        self.http_request(self.user, "get", f"articles/{article.id}")
        response = self.http_request(
            self.user,
            "patch",
            f"articles/{article.id}",
            {"title": new_title, "content": new_content},
        )
        assert response.status_code == status.HTTP_200_OK
        response = self.http_request(self.user, "get", f"articles/{article.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("title") == new_title
        assert response.data.get("content") == new_content

    @pytest.mark.usefixtures("set_kaist_articles")
    def test_update_hit_counts(self):
        updated_hit_count = self.article.hit_count + 1
        res = self.http_request(self.user2, "get", f"articles/{self.article.id}").data
        assert res.get("hit_count") == updated_hit_count
        assert Article.objects.get(id=self.article.id).hit_count == updated_hit_count

        # 권한 없는 사용자가 get
        self.http_request(self.non_kaist_user, "get", f"articles/{self.article.id}")

        res = self.http_request(self.user2, "get", f"articles/{self.article.id}").data
        assert res.get("hit_count") == updated_hit_count

    def test_delete_by_non_writer(self):
        # 글쓴이가 아닌 사람은 글을 지울 수 없음
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user2, "delete", f"articles/{self.article.id}")
        assert Article.objects.filter(id=self.article.id)

    def test_delete_by_writer(self):
        # 글쓴이는 본인 글을 지울 수 있음
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user, "delete", f"articles/{self.article.id}")
        assert not Article.objects.filter(id=self.article.id)

    def test_update_votes(self):
        # user가 만든 set_article의 positive vote, negative vote 를 set_user_client2를 이용해서 바꿈 (투표 취소 가능한지, 둘다 중복투표 불가능한지 확인)
        # positive vote 확인
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_positive"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # 같은 사람이 positive_vote 여러 번 투표할 수 없음
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_positive"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # positive_vote 취소
        self.http_request(self.user2, "post", f"articles/{self.article.id}/vote_cancel")
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        # positive_vote 취소 후 재투표
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_positive"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0
        self.http_request(self.user2, "post", f"articles/{self.article.id}/vote_cancel")

        # negative vote 확인
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_negative"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # 같은 사람이 negative vote 여러 번 투표할 수 없음
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_negative"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # negative vote 투표 취소
        self.http_request(self.user2, "post", f"articles/{self.article.id}/vote_cancel")
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        # negative vote 취소 후 재투표
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_negative"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # 중복 투표 시도 (negative 투표한 상태로 positive 투표하면, positive 1개로 바뀌어야함)
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_positive"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # 중복 투표 시도 (positive 투표한 상태로 negative 투표하면, negative 1개로 바뀌어야함)
        self.http_request(
            self.user2, "post", f"articles/{self.article.id}/vote_negative"
        )
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

    def test_self_vote(self):
        # 자신이 쓴 게시물은 좋아요 / 싫어요를 할 수 없음
        resp = self.http_request(
            self.user, "post", f"articles/{self.article.id}/vote_positive"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["message"] is not None
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        resp = self.http_request(
            self.user, "post", f"articles/{self.article.id}/vote_negative"
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert resp.data["message"] is not None
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

    @pytest.mark.usefixtures("set_readonly_board")
    def test_readonly_board(self):
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "name_type": NameType.REGULAR.name,
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_board": self.readonly_board.id,
        }
        response = self.http_request(self.user, "post", "articles", user_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_read_status(self):
        # user1, user2 모두 아직 안읽음
        res1 = self.http_request(self.user, "get", "articles")
        res2 = self.http_request(self.user2, "get", "articles")
        assert res1.data["results"][0]["read_status"] == "N"
        assert res2.data["results"][0]["read_status"] == "N"

        article_id = res1.data["results"][0]["id"]

        # user2만 읽음
        self.http_request(self.user2, "get", f"articles/{article_id}")
        res1 = self.http_request(self.user, "get", "articles")
        res2 = self.http_request(self.user2, "get", "articles")
        assert res1.data["results"][0]["read_status"] == "N"
        assert res2.data["results"][0]["read_status"] == "-"

        # user1이 업데이트 (user2은 아직 변경사항 확인못함)
        self.http_request(self.user, "get", f"articles/{article_id}")
        self.http_request(
            self.user, "patch", f"articles/{article_id}", {"content": "update!"}
        )

        # TODO: 현재는 프론트 구현상 게시물을 수정하면 바로 다시 GET을 호출하기 때문에 '-' 로 나옴.
        #       추후 websocket 등으로 게시물 수정이 실시간으로 이루어진다면, 'U'로 나오기 때문에 수정 필요.
        self.http_request(self.user, "get", f"articles/{article_id}")
        res1 = self.http_request(self.user, "get", "articles")
        assert res1.data["results"][0]["read_status"] == "-"

        res2 = self.http_request(self.user2, "get", "articles")
        assert res2.data["results"][0]["read_status"] == "U"

    # See #269
    def test_deleting_with_comments(self):
        self.article.comment_count = 1
        self.article.save()
        Comment.objects.create(
            content="this is a test comment",
            name_type=NameType.REGULAR,
            created_by=self.user,
            parent_article=self.article,
        )

        self.http_request(self.user, "delete", f"articles/{self.article.id}")
        self.article.refresh_from_db()

        assert (
            Comment.objects.filter(
                parent_article=self.article, deleted_at=MIN_TIME
            ).count()
            == 0
        )
        assert self.article.comment_count == 0

    def test_being_topped(self):
        """
        `Article.topped_at` is set when `Article.positive_vote_count >=
        Board.top_threshold`
        """
        THRESHOLD = 5
        board = Board.objects.create(top_threshold=THRESHOLD)
        article = Article.objects.create(created_by=self.user, parent_board=board)
        pk = article.pk

        users = Utils.create_users(THRESHOLD)
        *users_ex_one, last_user = users

        for user in users_ex_one:
            self.http_request(user, "post", f"articles/{pk}/vote_positive")

        article = Article.objects.get(pk=pk)
        assert article.positive_vote_count == THRESHOLD - 1
        assert article.topped_at is None

        self.http_request(last_user, "post", f"articles/{pk}/vote_positive")
        article = Article.objects.get(pk=pk)
        assert article.positive_vote_count == THRESHOLD
        assert article.topped_at is not None

    def test_top_ordered(self):
        """
        The most recently topped article must come first. If the same, then
        the most recent article must come first.
        """
        board = Board.objects.create()
        articles = [
            Article.objects.create(created_by=self.user, parent_board=board)
            for _ in range(3)
        ]

        time_early = timezone.datetime(2001, 10, 18)  # retro's birthday
        time_late = timezone.datetime(2003, 6, 17)  # yuwol's birthday

        articles[0].topped_at = time_early
        articles[1].topped_at = time_early
        articles[2].topped_at = time_late
        for article in articles:
            article.save()

        response = self.http_request(self.user, "get", "articles/top")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["num_items"] == 3

        oracle_indices = [2, 1, 0]
        for idx, res in zip(oracle_indices, response.data["results"]):
            assert articles[idx].pk == res["id"]


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_user_without_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
    "set_realname_article",
)
class TestRealnameArticle(TestCase, RequestSetting):
    def test_get_realname_article(self):
        # kaist info가 있는 유저가 생성한 게시글
        realname_article_with_kinfo = Article.objects.create(
            title="example realname article with kinfo",
            content="example realname content with kinfo",
            content_text="example realname content text with kinfo",
            name_type=NameType.REALNAME,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user_with_kaist_info,
            parent_topic=self.realname_topic,
            parent_board=self.realname_board,
            commented_at=timezone.now(),
        )

        # kaist info가 없는 유저가 생성한 게시글
        realname_article_without_kinfo = Article.objects.create(
            title="example realname article without_kinfo",
            content="example realname content without_kinfo",
            content_text="example realname content text without_kinfo",
            name_type=NameType.REALNAME,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user_without_kaist_info,
            parent_topic=self.realname_topic,
            parent_board=self.realname_board,
            commented_at=timezone.now(),
        )

        res = self.http_request(
            self.user_with_kaist_info,
            "get",
            f"articles/{realname_article_with_kinfo.id}",
        ).data
        assert res.get("name_type") == NameType.REALNAME
        assert (
            res.get("created_by")["username"]
            == realname_article_with_kinfo.created_by.profile.realname
        )

        res2 = self.http_request(
            self.user_without_kaist_info,
            "get",
            f"articles/{realname_article_without_kinfo.id}",
        ).data
        assert res2.get("name_type") == NameType.REALNAME
        assert (
            res2.get("created_by")["username"]
            == realname_article_without_kinfo.created_by.profile.realname
        )

    def test_create_realname_article(self):
        article_title = "realname article for test_create"
        article_data = {
            "title": article_title,
            "content": "realname content for test_create",
            "content_text": "realname content_text for test_create",
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": self.realname_topic.id,
            "parent_board": self.realname_board.id,
            "name_type": NameType.REALNAME.name,
        }

        result = self.http_request(
            self.user_with_kaist_info, "post", "articles", article_data
        ).data

        assert result.get("name_type") == NameType.REALNAME
        assert Article.objects.get(title=article_title).name_type == NameType.REALNAME

    def test_update_realname_article(self):
        article = Article.objects.create(
            title="realname article for test_create",
            content="realname content for test_create",
            content_text="realname content_text for test_create",
            name_type=NameType.REALNAME,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user_with_kaist_info,
            parent_topic=self.realname_topic,
            parent_board=self.realname_board,
            commented_at=timezone.now(),
        )
        article.save()

        new_title = "realname article for test_update"
        new_content = "realname content for test_update"
        result = self.http_request(
            self.user_with_kaist_info,
            "put",
            f"articles/{article.id}",
            {"title": new_title, "content": new_content},
        ).data

        assert result.get("name_type") == NameType.REALNAME
        assert Article.objects.get(title=new_title).name_type == NameType.REALNAME

    def test_ban_vote_cancellation_after_30(self):
        users = Utils.create_users(num=SCHOOL_RESPONSE_VOTE_THRESHOLD - 1)

        for user in users:
            self.http_request(
                user, "post", f"articles/{self.realname_article.id}/vote_positive"
            )

        res1 = self.http_request(
            self.user_without_kaist_info,
            "post",
            f"articles/{self.realname_article.id}/vote_positive",
        )
        article = Article.objects.get(id=self.realname_article.id)
        assert res1.status_code == status.HTTP_200_OK
        assert article.positive_vote_count == SCHOOL_RESPONSE_VOTE_THRESHOLD

        res2 = self.http_request(
            self.user_without_kaist_info,
            "post",
            f"articles/{self.realname_article.id}/vote_cancel",
        )
        article = Article.objects.get(id=self.realname_article.id)
        assert res2.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert article.positive_vote_count == SCHOOL_RESPONSE_VOTE_THRESHOLD


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_user_without_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
)
class TestHiddenArticles(TestCase, RequestSetting):
    @staticmethod
    def _user_factory(user_kwargs, profile_kwargs):
        user_instance, _ = User.objects.get_or_create(**user_kwargs)
        if not hasattr(user_instance, "profile"):
            UserProfile.objects.get_or_create(
                **{
                    **profile_kwargs,
                    "user": user_instance,
                    "agree_terms_of_service_at": timezone.now(),
                    "sso_user_info": {},
                }
            )
            UserGroup.objects.get_or_create(
                user=user_instance,
                group=Group.search_by_id(2),  # 2 = KAIST member
            )
        return user_instance

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_mind_user = cls._user_factory(
            {"username": "clean-mind-user", "email": "iamclean@sparcs.org"},
            {
                "nickname": "clean",
                "see_social": False,
                "see_sexual": False,
                "sso_user_info": {},
            },
        )
        cls.dirty_mind_user = cls._user_factory(
            {"username": "dirty-mind-user", "email": "kbdwarrior@sparcs.org"},
            {
                "nickname": "kbdwarrior",
                "see_social": True,
                "see_sexual": True,
                "sso_user_info": {},
            },
        )

    def _article_factory(
        self, is_content_sexual=False, is_content_social=False, **article_kwargs
    ):
        return Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            name_type=NameType.REGULAR,
            hit_count=0,
            is_content_sexual=is_content_sexual,
            is_content_social=is_content_social,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now(),
            **article_kwargs,
        )

    def _test_can_override(self, user: User, target_article: Article, expected: bool):
        res = self.http_request(
            user, "get", f"articles/{target_article.id}", None, "override_hidden"
        ).data
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert res.get("why_hidden") is not None
        assert res.get("why_hidden") != []
        assert res.get("is_hidden") != expected
        if expected:
            assert res.get("title") is not None
            assert res.get("content") is not None
        else:
            assert res.get("title") is None
            assert res.get("content") is None

    def test_sexual_article_block(self):
        target_article = self._article_factory(
            is_content_sexual=True, is_content_social=False
        )

        res = self.http_request(
            self.clean_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert res.get("is_content_sexual")
        assert res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert res.get("title") is None
        assert res.get("content") is None
        assert "ADULT_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.clean_mind_user, target_article, True)

    def test_sexual_article_pass(self):
        target_article = self._article_factory(
            is_content_sexual=True, is_content_social=False
        )

        res = self.http_request(
            self.dirty_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert res.get("is_content_sexual")
        assert res.get("can_override_hidden") is None
        assert not res.get("is_hidden")
        assert res.get("title") is not None
        assert res.get("content") is not None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert res.get("why_hidden") == []

    def test_social_article_block(self):
        target_article = self._article_factory(
            is_content_sexual=False, is_content_social=True
        )

        res = self.http_request(
            self.clean_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert "SOCIAL_CONTENT" in res.get("why_hidden")
        assert res.get("is_content_social")
        assert res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("content") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        self._test_can_override(self.clean_mind_user, target_article, True)

    def test_social_article_pass(self):
        target_article = self._article_factory(
            is_content_sexual=False, is_content_social=True
        )

        res = self.http_request(
            self.dirty_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert res.get("can_override_hidden") is None
        assert res.get("is_content_social")
        assert not res.get("is_hidden")
        assert res.get("title") is not None
        assert res.get("content") is not None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert res.get("why_hidden") == []

    def test_blocked_user_block(self):
        target_article = self._article_factory(
            is_content_sexual=False, is_content_social=False
        )
        Block.objects.create(blocked_by=self.clean_mind_user, user=self.user)

        res = self.http_request(
            self.clean_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("content") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert "BLOCKED_USER_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.clean_mind_user, target_article, True)

    def _create_report_hidden_article(self):
        return self._article_factory(report_count=1000000, hidden_at=timezone.now())

    def _create_deleted_article(self):
        return self._article_factory(deleted_at=timezone.now())

    def test_reported_article_block(self):
        target_article = self._create_report_hidden_article()

        res = self.http_request(
            self.clean_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert not res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("content") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert "REPORTED_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.clean_mind_user, target_article, False)

    def test_block_reason_order(self):
        target_article = self._article_factory(
            is_content_sexual=True,
            is_content_social=True,
            report_count=1000000,
            hidden_at=timezone.now(),
        )
        Block.objects.create(blocked_by=self.clean_mind_user, user=self.user)

        res = self.http_request(
            self.clean_mind_user, "get", f"articles/{target_article.id}"
        ).data
        assert res.get("is_hidden")
        assert res.get("why_hidden") == [
            "REPORTED_CONTENT",
            "BLOCKED_USER_CONTENT",
            "ADULT_CONTENT",
            "SOCIAL_CONTENT",
        ]

    def test_modify_deleted_article(self):
        target_article = self._create_deleted_article()

        new_content = "attempt to modify deleted article"
        res = self.http_request(
            self.user,
            "put",
            f"articles/{target_article.id}",
            {
                "title": new_content,
                "content": new_content,
                "content_text": new_content,
            },
        )

        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_modify_report_hidden_article(self):
        target_article = self._create_report_hidden_article()

        new_content = "attempt to modify hidden article"
        res = self.http_request(
            self.user,
            "put",
            f"articles/{target_article.id}",
            {
                "title": new_content,
                "content": new_content,
                "content_text": new_content,
            },
        )

        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_get_deleted_article(self):
        target_article = self._create_deleted_article()

        res = self.http_request(self.user2, "get", f"articles/{target_article.id}")
        assert res.status_code == 410

    def test_exclude_deleted_article_from_list(self):
        target_article = self._create_deleted_article()

        res = self.http_request(self.user2, "get", f"articles").data

        # user가 글 목록을 가져올 때, 삭제된 글이 목록에 없는 것 확인
        for post in res.get("results"):
            assert post.get("id") != target_article.id

    def test_delete_already_deleted_article(self):
        target_article = self._create_deleted_article()
        res = self.http_request(self.user, "delete", f"articles/{target_article.id}")
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_report_hidden_article(self):
        target_article = self._create_report_hidden_article()
        res = self.http_request(self.user, "delete", f"articles/{target_article.id}")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_vote_deleted_article(self):
        target_article = self._create_deleted_article()

        positive_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_positive"
        )
        assert positive_vote_result.status_code == status.HTTP_404_NOT_FOUND

        negative_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_negative"
        )
        assert negative_vote_result.status_code == status.HTTP_404_NOT_FOUND

        cancel_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_positive"
        )
        assert cancel_vote_result.status_code == status.HTTP_404_NOT_FOUND

    def test_vote_report_hidden_article(self):
        target_article = self._create_report_hidden_article()

        positive_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_positive"
        )
        assert positive_vote_result.status_code == status.HTTP_403_FORBIDDEN

        negative_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_negative"
        )
        assert negative_vote_result.status_code == status.HTTP_403_FORBIDDEN

        Vote.objects.create(
            voted_by=self.user2,
            parent_article=target_article,
            is_positive=True,
        )
        target_article.update_vote_status()

        cancel_vote_result = self.http_request(
            self.user2, "post", f"articles/{target_article.id}/vote_cancel"
        )
        assert cancel_vote_result.status_code == status.HTTP_403_FORBIDDEN
        assert Article.objects.get(id=target_article.id).positive_vote_count == 1

    def test_report_deleted_article(self):
        target_article = self._create_deleted_article()

        res = self.http_request(
            self.user2,
            "post",
            "reports",
            {
                "content": "This is a report",
                "parent_article": target_article.id,
            },
        )

        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_report_already_hidden_article(self):
        target_article = self._create_report_hidden_article()

        res = self.http_request(
            self.user2,
            "post",
            "reports",
            {
                "content": "This is a report",
                "parent_article": target_article.id,
            },
        )

        assert res.status_code == status.HTTP_403_FORBIDDEN
