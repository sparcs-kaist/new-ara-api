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

    request.cls.article1 = create_article(1)
    request.cls.article2 = create_article(2)
    request.cls.article3 = create_article(3)
    request.cls.article4 = create_article(4)
    request.cls.article5 = create_article(5)
    request.cls.article6 = create_article(6)
    request.cls.article7 = create_article(7)
    request.cls.article8 = create_article(8)
    request.cls.article9 = create_article(9)
    request.cls.article10 = create_article(10)


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_articles')
class TestRecent(TestCase, RequestSetting):
    def test_created_list(self):
        res = self.http_request(self.user, 'get', 'articles')
        assert res.data.get('num_items') == 10

    # 아무것도 읽지 않았을 때 recently_read는 empty array 임을 확인
    def test_recent_at_start(self):
        res = self.http_request(self.user, 'get', 'recent')
        assert res.data.get('recently_read') == []

    # article을 생 순서대로 읽었을 떄의 recent_articles 값 확인
    # GET 'recent'의 리턴 타입은 길이 5의 List[OrderedDict]임
    # OrderedDict의 array 임 (id, topic, create time 등 article의 모든 Field가 들어 있음)
    # array[0]이 가장 최근에 읽은 article 임
    def test_recent_order_written(self):
        self.http_request(self.user, 'get', f'articles/{self.article1.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article3.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article4.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article5.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article6.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article7.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article8.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data

        recent_list = self.http_request(self.user, 'get', 'recent').data.get('recently_read')
        print(recent_list)
        print(self.article1.id)
        print(self.article10.id)
        assert recent_list[0]['id'] == self.article10.id
        assert recent_list[1]['id'] == self.article9.id
        assert recent_list[2]['id'] == self.article8.id
        assert recent_list[3]['id'] == self.article7.id
        assert recent_list[4]['id'] == self.article6.id
        assert recent_list[5]['id'] == self.article5.id
        assert recent_list[6]['id'] == self.article4.id
        assert recent_list[7]['id'] == self.article3.id
        assert recent_list[8]['id'] == self.article2.id
        assert recent_list[9]['id'] == self.article1.id

    # article을 id 역순으로 읽었을 때의 recent_articles 값 확인
    def test_reverse_order_written(self):
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article8.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article7.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article6.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article5.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article4.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article3.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article1.id}').data

        recent_list = self.http_request(self.user, 'get', 'recent').data.get('recently_read')
        assert len(recent_list) == 10
        assert recent_list[0]['id'] == self.article1.id
        assert recent_list[1]['id'] == self.article2.id
        assert recent_list[2]['id'] == self.article3.id
        assert recent_list[3]['id'] == self.article4.id
        assert recent_list[4]['id'] == self.article5.id
        assert recent_list[5]['id'] == self.article6.id
        assert recent_list[6]['id'] == self.article7.id
        assert recent_list[7]['id'] == self.article8.id
        assert recent_list[8]['id'] == self.article9.id
        assert recent_list[9]['id'] == self.article10.id

    # 같은 article을 연속으로 여러번 읽었을 때 recent_articles
    def test_read_same_article_multiple_times_in_a_row(self):
        self.http_request(self.user, 'get', f'articles/{self.article1.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article3.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article4.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article5.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article6.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article7.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article8.id}').data

        # artcle9를 3번 읽음
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data

        # article10을 3번 읽음
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data

        recent_list = self.http_request(self.user, 'get', 'recent').data.get('recently_read')
        # recent list에는 article 9, 10이 한 번씩만 들어가 있는지 확인
        assert recent_list[0]['id'] == self.article10.id
        assert recent_list[1]['id'] == self.article9.id
        assert recent_list[2]['id'] == self.article8.id
        assert recent_list[3]['id'] == self.article7.id
        assert recent_list[4]['id'] == self.article6.id
        assert recent_list[5]['id'] == self.article5.id
        assert recent_list[6]['id'] == self.article4.id
        assert recent_list[7]['id'] == self.article3.id
        assert recent_list[8]['id'] == self.article2.id
        assert recent_list[9]['id'] == self.article1.id

    # 같은 article을 비연속적으로 여러번 읽었을 경우 확인 (전에 읽은 article 최근에 다시 읽었을 때)
    def test_read_same_article_multiple_times(self):
        # article 1부터 10까지 순서대로 읽기
        self.http_request(self.user, 'get', f'articles/{self.article1.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article3.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article4.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article5.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article6.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article7.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article8.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article9.id}').data
        self.http_request(self.user, 'get', f'articles/{self.article10.id}').data

        #artticle 3을 다시 읽기
        self.http_request(self.user, 'get', f'articles/{self.article3.id}').data
        recent_list = self.http_request(self.user, 'get', 'recent').data.get('recently_read')

        # recent list에는 article 3이 제일 최근에만 한번 들어가 있는지 확인
        assert recent_list[0]['id'] == self.article3.id
        assert recent_list[1]['id'] == self.article10.id
        assert recent_list[2]['id'] == self.article9.id
        assert recent_list[3]['id'] == self.article8.id
        assert recent_list[4]['id'] == self.article7.id
        assert recent_list[5]['id'] == self.article6.id
        assert recent_list[6]['id'] == self.article5.id
        assert recent_list[7]['id'] == self.article4.id
        assert recent_list[8]['id'] == self.article2.id
        assert recent_list[9]['id'] == self.article1.id