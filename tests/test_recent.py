import pytest
from django.test import TestCase
from apps.core.models import Article, Topic, Board, Comment, Report
from tests.conftest import RequestSetting
from django.utils import timezone


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug='test board',
        ko_name='테스트 게시판',
        en_name='Test Board',
        ko_description='테스트 게시판입니다',
        en_description='This is a board for testing'
    )


@pytest.fixture(scope='class')
def set_topic(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug='test topic',
        ko_name='테스트 토픽',
        en_name='Test Topic',
        ko_description='테스트용 토픽입니다',
        en_description='This is topic for testing',
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_articles(request):
    """set_topic, set_user_client 먼저 적용. article 10개 생성 """
    def create_article(n):
        return Article.objects.create(
            title=f'Test Article{n}',
            content=f'Content of test article {n}',
            content_text=f'Content_text of test article {n}',
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
    request.cls.articles = [create_article(i) for i in range(1, 11)]


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_articles')
class TestRecent(TestCase, RequestSetting):
    def test_created_list(self):
        res = self.http_request(self.user, 'get', 'articles')
        assert res.data.get('num_items') == 10

    # 아무것도 읽지 않았을 때 recently_read는 empty array 임을 확인
    def test_recent_at_start(self):
        res = self.http_request(self.user, 'get', 'recents')
        assert res.data.get('results') == []

    # article을 생 순서대로 읽었을 떄의 recent_articles 값 확인
    # GET 'recent'의 리턴 타입은 길이 5의 List[OrderedDict]임
    # OrderedDict의 array 임 (id, topic, create time 등 article의 모든 Field가 들어 있음)
    # array[0]이 가장 최근에 읽은 article 임
    def test_recent_order_written(self):
        for article in self.articles:
            r = self.http_request(self.user, 'get', f'articles/{article.id}').data

        recent_list = self.http_request(self.user, 'get', 'recents').data.get('results')
        assert len(recent_list) == 10
        for i in range(10):
            assert recent_list[i]['id'] == self.articles[9-i].id

    # article을 id 역순으로 읽었을 때의 recent_articles 값 확인
    def test_reverse_order_written(self):
        for article in reversed(self.articles):
            r = self.http_request(self.user, 'get', f'articles/{article.id}').data

        recent_list = self.http_request(self.user, 'get', 'recents').data.get('results')
        assert len(recent_list) == 10
        for i in range(10):
            assert recent_list[i]['id'] == self.articles[i].id

    # 같은 article을 연속으로 여러번 읽었을 때 recent_articles
    def test_read_same_article_multiple_times_in_a_row(self):
        for article in self.articles[:8]:
            r = self.http_request(self.user, 'get', f'articles/{article.id}').data

        # Article 9를 3번 읽음
        for _ in range(3):
            r = self.http_request(self.user, 'get', f'articles/{self.articles[8].id}').data

        # Article 10을 3번 읽음
        for _ in range(3):
            r = self.http_request(self.user, 'get', f'articles/{self.articles[9].id}').data

        recent_list = self.http_request(self.user, 'get', 'recents').data.get('results')
        assert len(recent_list) == 10
        # Article 9, 10이 한 번씩만 들어가 있는지 확인
        for i in range(10):
            assert recent_list[i]['id'] == self.articles[9-i].id
        recent_list = self.http_request(self.user, 'get', 'recents').data.get('recently_read')

    # 같은 article을 비연속적으로 여러번 읽었을 경우 확인 (전에 읽은 article 최근에 다시 읽었을 때)
    def test_read_same_article_multiple_times(self):
        # Article 1부터 10까지 순서대로 읽기
        for article in self.articles:
            r = self.http_request(self.user, 'get', f'articles/{article.id}').data

        # Article 3을 다시 읽기
        r = self.http_request(self.user, 'get', f'articles/{self.articles[2].id}').data
        recent_list = self.http_request(self.user, 'get', 'recents').data.get('results')

        expected_order = [2, 9, 8, 7, 6, 5, 4, 3, 1, 0]
        for i in range(10):
            assert recent_list[i]['id'] == self.articles[expected_order[i]].id
