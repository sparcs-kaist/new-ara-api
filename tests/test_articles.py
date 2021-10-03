import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.core.models import Article, Topic, Board, Block
from apps.user.models import UserProfile
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
        ko_description="테스트 게시판입니다",
        en_description="This is a board for testing"
    )


@pytest.fixture(scope='class')
def set_topic(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug="test topic",
        ko_name="테스트 토픽",
        en_name="Test Topic",
        ko_description="테스트용 토픽입니다",
        en_description="This is topic for testing",
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_article(request):
    """set_board 먼저 적용"""
    request.cls.article = Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=False,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=request.cls.user,
            parent_topic=request.cls.topic,
            parent_board=request.cls.board,
            commented_at=timezone.now()
    )


@pytest.fixture(scope='function')
def set_kaist_articles(request):
    request.cls.non_kaist_user, _ = User.objects.get_or_create(username='NonKaistUser', email='non-kaist-user@sparcs.org')
    if not hasattr(request.cls.non_kaist_user, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.non_kaist_user, nickname='Not a KAIST User', agree_terms_of_service_at=timezone.now())
    request.cls.kaist_user, _ = User.objects.get_or_create(username='KaistUser', email='kaist-user@sparcs.org')
    if not hasattr(request.cls.kaist_user, 'profile'):
        UserProfile.objects.get_or_create(user=request.cls.kaist_user, nickname='KAIST User',
                                          group=UserProfile.UserGroup.KAIST_MEMBER, agree_terms_of_service_at=timezone.now())

    request.cls.kaist_board, _ = Board.objects.get_or_create(
        slug="kaist-only",
        ko_name="KAIST Board",
        en_name="KAIST Board",
        ko_description="KAIST Board",
        en_description="KAIST Board",
        access_mask=2
    )
    request.cls.kaist_article, _ = Article.objects.get_or_create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=False,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=request.cls.user,
            parent_board=request.cls.kaist_board,
            commented_at=timezone.now()
    )
    yield None
    request.cls.kaist_board.delete()
    request.cls.kaist_article.delete()


@pytest.fixture(scope='function')
def set_readonly_board(request):
    request.cls.readonly_board, _ = Board.objects.get_or_create(
        slug="readonly",
        ko_name="읽기전용 게시판",
        en_name="Read Only Board",
        ko_description="테스트 게시판입니다",
        en_description="This is a board for testing",
        is_readonly=True
    )
    yield None
    request.cls.readonly_board.delete()


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_article')
class TestArticle(TestCase, RequestSetting):
    def test_list(self):
        # article 개수를 확인하는 테스트
        res = self.http_request(self.user, 'get', 'articles')
        assert res.data.get('num_items') == 1

        Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=False,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now()
        )

        Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=False,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now()
        )

        res = self.http_request(self.user, 'get', 'articles')
        assert res.data.get('num_items') == 3

    def test_get(self):
        # article 조회가 잘 되는지 확인
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('title') == self.article.title
        assert res.get('content') == self.article.content
        assert res.get('is_anonymous') == self.article.is_anonymous
        assert res.get('is_content_sexual') == self.article.is_content_sexual
        assert res.get('is_content_social') == self.article.is_content_social
        assert res.get('positive_vote_count') == self.article.positive_vote_count
        assert res.get('negative_vote_count') == self.article.negative_vote_count
        assert res.get('created_by')['username'] == self.user.username
        assert res.get('parent_topic')['ko_name'] == self.article.parent_topic.ko_name
        assert res.get('parent_board')['ko_name'] == self.article.parent_board.ko_name

    # http get으로 익명 게시글을 retrieve했을 때 작성자가 익명으로 나타나는지 확인
    def test_anonymous_article(self):
        # 익명 게시글 생성
        anon_article = Article.objects.create(
            title="example anonymous article",
            content="example anonymous content",
            content_text="example anonymous content text",
            is_anonymous=True,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now()
        )

        # 익명 게시글을 GET할 때, 작성자의 정보가 전달되지 않는 것 확인
        res = self.http_request(self.user, 'get', f'articles/{anon_article.id}').data
        assert res.get('is_anonymous')
        assert res.get('created_by')['username'] != anon_article.created_by.username

        res2 = self.http_request(self.user2, 'get', f'articles/{anon_article.id}').data
        assert res2.get('is_anonymous')
        assert res2.get('created_by')['username'] != anon_article.created_by.username

    def test_create(self):
        # test_create: HTTP request (POST)를 이용해서 생성
        # user data in dict
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "is_anonymous": True,
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": self.topic.id,
            "parent_board": self.board.id
        }
        # convert user data to JSON
        self.http_request(self.user, 'post', 'articles', user_data)
        assert Article.objects.filter(title='article for test_create')

    def test_update_cache_sync(self):
        new_title = 'title changed!'
        new_content = 'content changed!'
        article = Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=True,
            is_content_sexual=False,
            is_content_social=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now()
        )
        # 캐시 업데이트 확인을 위해 GET을 미리 한번 함
        self.http_request(self.user, 'get', f'articles/{article.id}')
        response = self.http_request(self.user, 'put', f'articles/{article.id}', {
            'title': new_title,
            'content': new_content
        })
        assert response.status_code == 200
        response = self.http_request(self.user, 'get', f'articles/{article.id}')
        assert response.status_code == 200
        assert response.data.get('title') == new_title
        assert response.data.get('content') == new_content

    def test_update_hit_counts(self):
        previous_hit_count = self.article.hit_count
        res = self.http_request(self.user2, 'get', f'articles/{self.article.id}').data
        assert res.get('hit_count') == previous_hit_count + 1
        assert Article.objects.get(id=self.article.id).hit_count == previous_hit_count + 1

    def test_delete_by_non_writer(self):
        # 글쓴이가 아닌 사람은 글을 지울 수 없음
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user2, 'delete', f'articles/{self.article.id}')
        assert Article.objects.filter(id=self.article.id)

    def test_delete_by_writer(self):
        # 글쓴이는 본인 글을 지울 수 있음
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user, 'delete', f'articles/{self.article.id}')
        assert not Article.objects.filter(id=self.article.id)

    def test_update_votes(self):
        # user가 만든 set_article의 positive vote, negative vote 를 set_user_client2를 이용해서 바꿈 (투표 취소 가능한지, 둘다 중복투표 불가능한지 확인)
        # positive vote 확인
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_positive')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # 같은 사람이 positive_vote 여러 번 투표할 수 없음
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_positive')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # positive_vote 취소
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_cancel')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        # positive_vote 취소 후 재투표
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_positive')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_cancel')

        # negative vote 확인
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_negative')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # 같은 사람이 negative vote 여러 번 투표할 수 없음
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_negative')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # negative vote 투표 취소
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_cancel')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        # negative vote 취소 후 재투표
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_negative')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

        # 중복 투표 시도 (negative 투표한 상태로 positive 투표하면, positive 1개로 바뀌어야함)
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_positive')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 1
        assert article.negative_vote_count == 0

        # 중복 투표 시도 (positive 투표한 상태로 negative 투표하면, negative 1개로 바뀌어야함)
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_negative')
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 1

    def test_self_vote(self):
        # 자신이 쓴 게시물은 좋아요 / 싫어요를 할 수 없음
        resp = self.http_request(self.user, 'post', f'articles/{self.article.id}/vote_positive')
        assert resp.status_code == 403
        assert resp.data["message"] is not None
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

        resp = self.http_request(self.user, 'post', f'articles/{self.article.id}/vote_negative')
        assert resp.status_code == 403
        assert resp.data["message"] is not None
        article = Article.objects.get(id=self.article.id)
        assert article.positive_vote_count == 0
        assert article.negative_vote_count == 0

    @pytest.mark.usefixtures('set_kaist_articles')
    def test_kaist_permission(self):
        # 카이스트 구성원만 볼 수 있는 게시판에 대한 테스트
        def check_kaist_error(response):
            assert response.status_code == 403
            assert 'KAIST' in response.data['detail']  # 에러 메세지 체크
        # 게시물 읽기 테스트
        check_kaist_error(self.http_request(self.non_kaist_user, 'get', f'articles/{self.kaist_article.id}'))
        # 투표 테스트
        check_kaist_error(
            self.http_request(self.non_kaist_user, 'post', f'articles/{self.kaist_article.id}/vote_positive')
        )
        check_kaist_error(
            self.http_request(self.non_kaist_user, 'post', f'articles/{self.kaist_article.id}/vote_negative')
        )
        check_kaist_error(
            self.http_request(self.non_kaist_user, 'post', f'articles/{self.kaist_article.id}/vote_cancel')
        )

    @pytest.mark.usefixtures('set_readonly_board')
    def test_readonly_board(self):
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "is_anonymous": True,
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_board": self.readonly_board.id
        }
        response = self.http_request(self.user, 'post', 'articles', user_data)
        assert response.status_code == 400

    def test_read_status(self):
        # user1, user2 모두 아직 안읽음
        res1 = self.http_request(self.user, 'get', 'articles')
        res2 = self.http_request(self.user2, 'get', 'articles')
        assert res1.data['results'][0]['read_status'] == 'N'
        assert res2.data['results'][0]['read_status'] == 'N'

        # user2만 읽음
        self.http_request(self.user2, 'get', f'articles/{self.article.id}')
        res1 = self.http_request(self.user, 'get', 'articles')
        res2 = self.http_request(self.user2, 'get', 'articles')
        assert res1.data['results'][0]['read_status'] == 'N'
        assert res2.data['results'][0]['read_status'] == '-'

        # user1이 업데이트 (user2은 아직 변경사항 확인못함)
        self.http_request(self.user, 'get', f'articles/{self.article.id}')
        self.http_request(self.user, 'patch', f'articles/{self.article.id}', {'content': 'update!'})

        # TODO: 현재는 프론트 구현상 게시물을 수정하면 바로 다시 GET을 호출하기 때문에 '-' 로 나옴.
        #       추후 websocket 등으로 게시물 수정이 실시간으로 이루어진다면, 'U'로 나오기 때문에 수정 필요.
        self.http_request(self.user, 'get', f'articles/{self.article.id}')
        res1 = self.http_request(self.user, 'get', 'articles')
        assert res1.data['results'][0]['read_status'] == '-'

        res2 = self.http_request(self.user2, 'get', 'articles')
        assert res2.data['results'][0]['read_status'] == 'U'


@pytest.mark.usefixtures('set_user_client', 'set_board', 'set_topic', 'set_article')
class TestHiddenArticles(TestCase, RequestSetting):
    @staticmethod
    def _user_factory(user_kwargs, profile_kwargs):
        user_instance, _ = User.objects.get_or_create(**user_kwargs)
        if not hasattr(user_instance, 'profile'):
            UserProfile.objects.get_or_create(**{
                **profile_kwargs,
                'user': user_instance,
                'agree_terms_of_service_at': timezone.now(),
                'group': UserProfile.UserGroup.KAIST_MEMBER
            })
        return user_instance

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_mind_user = cls._user_factory(
            {'username': 'clean-mind-user', 'email': 'iamclean@sparcs.org'},
            {'nickname': 'clean', 'see_social': False, 'see_sexual': False}
        )
        cls.dirty_mind_user = cls._user_factory(
            {'username': 'dirty-mind-user', 'email': 'kbdwarrior@sparcs.org'},
            {'nickname': 'kbdwarrior', 'see_social': True, 'see_sexual': True}
        )

    def _article_factory(self, **article_kwargs):
        return Article.objects.create(
            title="example article",
            content="example content",
            content_text="example content text",
            is_anonymous=False,
            hit_count=0,
            positive_vote_count=0,
            negative_vote_count=0,
            created_by=self.user,
            parent_topic=self.topic,
            parent_board=self.board,
            commented_at=timezone.now(),
            **article_kwargs
        )

    def _test_can_override(self, user: User, target_article: Article, expected: bool):
        res = self.http_request(user, 'get', f'articles/{target_article.id}', None, 'override_hidden').data
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert res.get('why_hidden') is not None
        assert res.get('why_hidden') != []
        assert res.get('is_hidden') != expected
        if expected:
            assert res.get('title') is not None
            assert res.get('content') is not None
        else:
            assert res.get('title') is None
            assert res.get('content') is None

    def test_sexual_article_block(self):
        target_article = self._article_factory(
            is_content_sexual=True,
            is_content_social=False
        )

        res = self.http_request(self.clean_mind_user, 'get', f'articles/{target_article.id}').data
        assert res.get('is_content_sexual')
        assert res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert res.get('title') is None
        assert res.get('content') is None
        assert 'ADULT_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.clean_mind_user, target_article, True)

    def test_sexual_article_pass(self):
        target_article = self._article_factory(
            is_content_sexual=True,
            is_content_social=False
        )

        res = self.http_request(self.dirty_mind_user, 'get', f'articles/{target_article.id}').data
        assert res.get('is_content_sexual')
        assert res.get('can_override_hidden') is None
        assert not res.get('is_hidden')
        assert res.get('title') is not None
        assert res.get('content') is not None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert res.get('why_hidden') == []

    def test_social_article_block(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=True
        )

        res = self.http_request(self.clean_mind_user, 'get', f'articles/{target_article.id}').data
        assert 'SOCIAL_CONTENT' in res.get('why_hidden')
        assert res.get('is_content_social')
        assert res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('content') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        self._test_can_override(self.clean_mind_user, target_article, True)

    def test_social_article_pass(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=True
        )

        res = self.http_request(self.dirty_mind_user, 'get', f'articles/{target_article.id}').data
        assert res.get('can_override_hidden') is None
        assert res.get('is_content_social')
        assert not res.get('is_hidden')
        assert res.get('title') is not None
        assert res.get('content') is not None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert res.get('why_hidden') == []

    def test_blocked_user_block(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=False
        )
        Block.objects.create(
            blocked_by=self.clean_mind_user,
            user=self.user
        )

        res = self.http_request(self.clean_mind_user, 'get', f'articles/{target_article.id}').data
        assert res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('content') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert 'BLOCKED_USER_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.clean_mind_user, target_article, True)

    def test_reported_article_block(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=False,
            report_count=1000000,
            hidden_at=timezone.now()
        )

        res = self.http_request(self.clean_mind_user, 'get', f'articles/{target_article.id}').data
        assert not res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('content') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert 'REPORTED_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.clean_mind_user, target_article, False)

    def test_modify_deleted_article(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=False,
        )

        self.http_request(self.user, 'delete', f'articles/{target_article.id}')

        new_content = "attempt to modify deleted article"
        res = self.http_request(self.user, 'put', f'articles/{target_article.id}', {
            "title": new_content,
            "content": new_content,
            "content_text": new_content,
        })

        assert res.status_code == 404

    def test_modify_report_hidden_article(self):
        target_article = self._article_factory(
            is_content_sexual=False,
            is_content_social=False,
            report_count=1000000,
            hidden_at=timezone.now()
        )

        new_content = "attempt to modify hidden article"
        res = self.http_request(self.user, 'put', f'articles/{target_article.id}', {
            "title": new_content,
            "content": new_content,
            "content_text": new_content,
        })

        assert res.status_code == 405
