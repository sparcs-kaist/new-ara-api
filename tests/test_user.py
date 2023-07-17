from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone

from apps.core.models import Article, Board, Comment
from apps.core.models.board import NameType
from ara.settings import MIN_TIME
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope="class")
def set_boards(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
    )

    request.cls.realname_board = Board.objects.create(
        slug="realname",
        ko_name="실명 게시판",
        en_name="Realname Board",
        name_type=NameType.REALNAME,
    )


@pytest.fixture(scope="class")
def set_articles(request):
    """set_board, set_user_client2 먼저 적용"""
    common_kwargs = {
        "content": "example content",
        "content_text": "example content text",
        "name_type": NameType.REGULAR,
        "created_by": request.cls.user2,
        "parent_board": request.cls.board,
        "hit_count": 0,
        # Topic is nullable
    }
    # 키: Article ID, 값: (성인글 여부, 정치글 여부,) 의 tuple
    # 글목록 테스트 때 빠른 lookup을 위해 사용합니다.
    request.cls.articles_meta = {}
    request.cls.article_clean = Article.objects.create(
        title="클린한 게시물",
        is_content_sexual=False,
        is_content_social=False,
        commented_at=timezone.now(),
        **common_kwargs,
    )
    request.cls.article_sexual = Article.objects.create(
        title="성인글",
        is_content_sexual=True,
        is_content_social=False,
        commented_at=timezone.now(),
        **common_kwargs,
    )
    request.cls.article_social = Article.objects.create(
        title="정치글", is_content_sexual=False, is_content_social=True, **common_kwargs
    )
    request.cls.article_sexual_and_social = Article.objects.create(
        title="정치+성인글", is_content_sexual=True, is_content_social=True, **common_kwargs
    )

    request.cls.articles_meta[request.cls.article_clean.id] = (False, False)
    request.cls.articles_meta[request.cls.article_sexual.id] = (True, False)
    request.cls.articles_meta[request.cls.article_social.id] = (False, True)
    request.cls.articles_meta[request.cls.article_sexual_and_social.id] = (True, True)


@pytest.fixture(scope="class")
def set_anonymous_article(request):
    """set_board, set_user_client2 먼저 적용"""
    request.cls.article_anonymous = Article.objects.create(
        title="익명글",
        is_content_sexual=False,
        is_content_social=False,
        name_type=NameType.ANONYMOUS,
        content="example content",
        content_text="example content text",
        created_by=request.cls.user2,
        parent_board=request.cls.board,
        hit_count=0,
    )


@pytest.fixture(scope="class")
def set_realname_article(request):
    """set_realname_board, set_user_with_kaist_info 먼저 적용"""
    request.cls.realname_article = Article.objects.create(
        title="실명글",
        is_content_sexual=False,
        is_content_social=False,
        name_type=NameType.REALNAME,
        content="example content",
        content_text="example content text",
        created_by=request.cls.user_with_kaist_info,
        parent_board=request.cls.realname_board,
        hit_count=0,
    )


@pytest.fixture(scope="class")
def set_anonymous_comment(request):
    """set_anonymous_articles 먼저 적용"""
    request.cls.comment_anonymous = Comment.objects.create(
        content="example comment",
        name_type=NameType.ANONYMOUS,
        created_by=request.cls.user,
        parent_article=request.cls.article_anonymous,
    )


@pytest.fixture(scope="class")
def set_realname_comment(request):
    """set_realname_article, set_user_with_kaist_info 먼저 적용"""
    request.cls.realname_comment = Comment.objects.create(
        content="example comment",
        name_type=NameType.REALNAME,
        created_by=request.cls.user_with_kaist_info,
        parent_article=request.cls.realname_article,
    )


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_boards",
    "set_articles",
)
class TestUser(TestCase, RequestSetting):
    def test_profile_edit(self):
        # 프로필 (ie. 사용자 설정)이 잘 변경되는지 테스트합니다.
        res = self.http_request(self.user, "get", f"user_profiles/{self.user.id}")
        assert res.status_code == 200
        assert res.data.get("see_sexual") == self.user.profile.see_sexual
        assert res.data.get("see_social") == self.user.profile.see_social
        assert res.data.get("nickname") == self.user.profile.nickname

        update_data = {
            "see_sexual": True,
            "see_social": True,
        }
        res = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert res.status_code == 200
        res = self.http_request(self.user, "get", f"user_profiles/{self.user.id}")
        assert res.data.get("see_sexual")
        assert res.data.get("see_social")

    def test_filter_articles_list(self):
        # 사용자의 게시물 필터에 따라 게시물 목록에서 필터링이 잘 되는지 테스트합니다.
        def single_case(see_sexual: bool, see_social: bool):
            self.user.profile.see_sexual = see_sexual
            self.user.profile.see_social = see_social

            resp = self.http_request(
                self.user,
                "get",
                "articles",
                querystring=f"parent_board={self.board.id}",
            ).data
            # 목록에 fixture 에서 설정한 게시물만 들어가 있는지 확인
            for post in resp.get("results"):
                hidden = post.get("is_hidden")
                post_id = post.get("id")
                is_sexual, is_social = self.articles_meta[post_id]
                assert hidden == (
                    (is_sexual and not see_sexual) or (is_social and not see_social)
                )

        single_case(True, True)
        single_case(True, False)
        single_case(False, True)
        single_case(False, False)

    def test_filter_articles_read(self):
        # 사용자의 게시물 필터에 따라 게시물 조회에서 필터링이 잘 되는지 테스트합니다.
        def single_case(see_sexual: bool, see_social: bool):
            self.user.profile.see_sexual = see_sexual
            self.user.profile.see_social = see_social

            for article_id, meta in self.articles_meta.items():
                resp = self.http_request(
                    self.user, "get", f"articles/{article_id}"
                ).data
                hidden = resp.get("is_hidden")
                is_sexual, is_social = meta
                assert hidden == (
                    (is_sexual and not see_sexual) or (is_social and not see_social)
                )

        single_case(True, True)
        single_case(True, False)
        single_case(False, True)
        single_case(False, False)

    # TODO: home/ view에서 best_articles 에서 어떻게 나오는지 확인하는 함수도 필요


@pytest.mark.usefixtures("set_user_client")
class TestUserNickname(TestCase, RequestSetting):
    def test_nickname_update(self):
        # 사용자가 처음 생성됨 -> 변경된 적이 없으므로 None
        assert self.user.profile.nickname_updated_at == MIN_TIME

        # 닉네임 변경시 nickname_updated_at 변경
        update_data = {
            "see_sexual": False,
            "see_social": False,
            "nickname": "foo",
        }
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert r.status_code == 200
        self.user.refresh_from_db()
        assert self.user.profile.nickname == "foo"
        assert (
            timezone.now() - self.user.profile.nickname_updated_at
        ).total_seconds() < 5

        # 닉네임이 현재 닉네임과 동일하다면 오류가 발생하지 않음
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert r.status_code == 200

        # 닉네임이 다르다면 오류 발생
        update_data["nickname"] = "bar"
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert r.status_code != 200

        # 3개월이 좀 안됐을 경우 오류 발생
        self.user.profile.nickname_updated_at -= timedelta(days=60)
        self.user.profile.save()
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert r.status_code != 200

        # 3개월 이전일 경우 정상적으로 변경
        self.user.profile.nickname_updated_at -= timedelta(days=33)
        self.user.profile.save()
        r = self.http_request(
            self.user, "put", f"user_profiles/{self.user.id}", data=update_data
        )
        assert r.status_code == 200
        self.user.refresh_from_db()
        assert self.user.profile.nickname == "bar"
        assert (
            timezone.now() - self.user.profile.nickname_updated_at
        ).total_seconds() < 5


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_boards",
    "set_anonymous_article",
    "set_anonymous_comment",
)
class TestAnonymousUser(TestCase, RequestSetting):
    def test_anonymous_article_profile_picture(self):
        r = self.http_request(
            self.user, "get", f"articles/{self.article_anonymous.id}"
        ).data
        profile_picture_url = r.get("created_by")["profile"]["picture"]
        try:
            URLValidator()(profile_picture_url)
        except ValidationError:
            assert False, "Bad URL for anonymous article profile picture"

    def test_anonymous_comment_profile_picture(self):
        r = self.http_request(
            self.user, "get", f"comments/{self.comment_anonymous.id}"
        ).data
        profile_picture_url = r.get("created_by")["profile"]["picture"]
        try:
            URLValidator()(profile_picture_url)
        except ValidationError:
            assert False, "Bad URL for anonymous comment profile picture"


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_boards",
    "set_realname_article",
    "set_realname_comment",
)
class TestRealnameUser(TestCase, RequestSetting):
    def test_realname_article_profile_picture(self):
        r = self.http_request(
            self.user_with_kaist_info, "get", f"articles/{self.realname_article.id}"
        ).data
        profile_picture_url = r.get("created_by")["profile"]["picture"]
        try:
            URLValidator()(profile_picture_url)
        except ValidationError:
            assert False, "Bad URL for anonymous article profile picture"

    def test_realname_comment_profile_picture(self):
        r = self.http_request(
            self.user_with_kaist_info, "get", f"comments/{self.realname_comment.id}"
        ).data
        profile_picture_url = r.get("created_by")["profile"]["picture"]
        try:
            URLValidator()(profile_picture_url)
        except ValidationError:
            assert False, "Bad URL for anonymous comment profile picture"
