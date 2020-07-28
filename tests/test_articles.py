import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Article, ArticleReadLog, Topic, Board, Comment
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


@pytest.fixture(scope='function')
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


@pytest.mark.usefixtures('set_user_client', 'set_board', 'set_topic')
class TestArticle(TestCase, RequestSetting):

    # TODO: 밑의 test함수에서 create_article을 사용하려고 하니, create_article을 못찾겠다고 함. 계속 같은 코드를 쓰지 않기 위해서, 이 문제 해결해야함
    def create_article(self):
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

    # article 개수를 확인하는 테스트
    def test_list(self):
        assert self.http_request('get', 'articles').data.get('num_items') == 0

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

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 1

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

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 2

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

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 3

    # article retrieve가 잘 되는지 확인
    @pytest.mark.usefixtures('set_article')
    def test_get(self):
        res = self.http_request('get', f'articles/{self.article.id}').data

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

        assert self.http_request('get', f'articles/{article.id}').data.get('created_by') == '익명'

    # hit_count, positive/negative votes, comments_count가 잘 업데이트 되는지 테스트
    def test_update_numbers(self):
        article = Article.objects.create(
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

        a = self.http_request('get', 'articles').data.get('results')[0]

        # test update_hit_count

        # originally, hit_count 0
        assert a.get('hit_count') == 0

        # TODO: HTTP request로 hit_count 증가하는 방법이 있을 것 같음. 직접 article read log 만들 필요 없을 것 같음. 이 다른 방법 찾기
        # creating ArticleReadLog increments hit_count by 1
        article_read_log = ArticleReadLog.objects.create(read_by=self.user2,
                                                         article=article)
        article.update_hit_count()
        a = self.http_request('get', 'articles').data.get('results')[0]
        assert a.get('hit_count') == 1

        # test vote count
        assert a.get('positive_vote_count') == 0
        assert a.get('negative_vote_count') == 0

        article_id_str = str(article.id)

        # TODO: POST request로 vote_positive를 부를 때, 유저 정보 전달하는 방법 찾기
        # 현재는 누적이 안되고 count가 0이나 1만 되어서, 계속 같은 유저로 들어가는 것 같음
        self.http_request('post', 'articles/' + article_id_str + '/vote_positive')

        a = self.http_request('get', 'articles').data.get('results')[0]
        assert a.get('positive_vote_count') == 1
        assert a.get('negative_vote_count') == 0

        self.http_request('post', 'articles/' + article_id_str + '/vote_negative')

        a = self.http_request('get', 'articles').data.get('results')[0]
        assert a.get('positive_vote_count') == 0
        assert a.get('negative_vote_count') == 1

        # test comments_count
        assert article.comments_count == 0
        Comment.objects.create(content='Sample comment',
                               is_anonymous=True,
                               positive_vote_count=4,
                               negative_vote_count=3,
                               created_by=self.user,
                               parent_article=article)
        a = self.http_request('get', 'articles').data.get('results')[0]
        assert a.get('comments_count') == 1

        Comment.objects.create(content='Sample comment',
                               is_anonymous=True,
                               positive_vote_count=4,
                               negative_vote_count=3,
                               created_by=self.user,
                               parent_article=article)
        a = self.http_request('get', 'articles').data.get('results')[0]
        assert a.get('comments_count') == 2

