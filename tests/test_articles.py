import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Article, Topic, Board
from tests.conftest import RequestSetting


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


@pytest.mark.usefixtures('set_user_client', 'set_board', 'set_topic', 'set_article')
class TestArticle(TestCase, RequestSetting):

    # article 개수를 확인하는 테스트
    def test_list(self):
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


    # article retrieve가 잘 되는지 확인
    def test_get(self):
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data

        assert res.get('title') == self.article.title
        assert res.get('content') == self.article.content
        assert res.get('content_text') == self.article.content_text
        assert res.get('is_anonymous') == self.article.is_anonymous
        assert res.get('is_content_sexual') == self.article.is_content_sexual
        assert res.get('is_content_social') == self.article.is_content_social
        assert res.get('positive_vote_count') == self.article.positive_vote_count
        assert res.get('negative_vote_count') == self.article.negative_vote_count
        assert res.get('created_by')['username'] == self.user.username
        assert res.get('parent_topic')['ko_name'] == self.article.parent_topic.ko_name
        assert res.get('parent_board')['ko_name'] == self.article.parent_board.ko_name

    # 익명의 글쓴이가 익명임을 확인
    def test_anonymous_writer(self):

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

        assert self.http_request(self.user, 'get', f'articles/{article.id}').data.get('created_by') == '익명'

    # TODO(jessie)
    '''
    - set_user_client2 fixture의 scope를 function으로 바꿨기 때문에, 사용하는 function 위에 usefixtures 하면 됩니다.
    - 1~5 모두 HTTP get request가 아닌 Article.objects.get(~~) 으로 확인
    
    1. test_create: HTTP request (POST)를 이용해서 생성
    2. test_update_hitcount: user가 만든 set_article의 hitcount를 set_user_client2를 이용해서 바꿈 (set_article retrieve)
    3. test_update_votes: user가 만든 set_article의 positive vote, negative vote 를 set_user_client2를 이용해서 바꿈 (투표 취소 가능한지, 둘다 중복투표 불가능한지 확인)
    4. test_delete: user가 만든 set_article을 본인이 지울때 잘 지워지는지
    5. test_delete_different_user: user가 만든 set_article을 set_user_client2를 이용해서 지웠을 때 안지워지는지
    +) comments count는 comments의 test 파일에서 학인합시다.
    '''


    # TODO: article이 HTTP request로 어떤 함수들을 거쳐 생성되는지 잘 이해가 되지 않습니다.
    ''' 
    conftest를 보고, 생성 정보는 JSON 형식으로, data field로 보낸다고 생각했습니다.
    viewsets/article.py를 보고, path는 'article/create'라고 생각했습니다.
    ArticleViewSet에서 perform_create는 serializer.save(created_by=self.request.user,)
    이렇게 구성되어있습니다.
    이 코드로 어떻게 article이 만들어지는지 잘 이해가 되지 않습니다.
    우선 parent_topic과 parent_board는 각각의 id를 넣어보았습니다. 
    현재 http_request(self.user, 'post', 'articles/create')가 405 response입니다.
    '''
    # test_create: HTTP request (POST)를 이용해서 생성
    def test_create(self):
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

    @pytest.mark.usefixtures('set_user_client2')
    def test_update_hitcounts(self):
        previous_hitcount = self.article.hit_count
        res = self.http_request(self.user2, 'get', f'articles/{self.article.id}').data
        assert res.get('hit_count') == previous_hitcount + 1
        assert Article.objects.get(id=self.article.id).hit_count == previous_hitcount + 1

    # 글쓴이가 아닌 사람은 글을 지울 수 없음
    @pytest.mark.usefixtures('set_user_client2')
    def test_delete_by_nonwriter(self):
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user2, 'delete', f'articles/{self.article.id}')
        assert Article.objects.filter(id=self.article.id)

    # 글쓴이는 본인 글을 지울 수 있음
    def test_delete_by_writer(self):
        assert Article.objects.filter(id=self.article.id)
        self.http_request(self.user, 'delete', f'articles/{self.article.id}')
        assert not Article.objects.filter(id=self.article.id)

    # user가 만든 set_article의 positive vote, negative vote 를 set_user_client2를 이용해서 바꿈 (투표 취소 가능한지, 둘다 중복투표 불가능한지 확인)
    @pytest.mark.usefixtures('set_user_client2')
    def test_update_votes(self):
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
