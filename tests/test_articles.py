import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Vote, Article, ArticleReadLog, Topic, Board, Comment
from tests.conftest import RequestSetting


@pytest.mark.usefixtures('set_user_clients')
class TestArticle(TestCase, RequestSetting):

    # article 개수를 확인하는 테스트
    def test_list(self):
        board = Board.objects.create(slug="board_example",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="보드입니다",
                                     en_description="This is board")

        topic = Topic.objects.create(slug="topic_example",
                                     ko_name="토픽1",
                                     en_name="topic1",
                                     ko_description="토픽입니",
                                     en_description="This is topic",
                                     parent_board=board)

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 0

        Article.objects.create(title="example article",
                               content="example content",
                               content_text="example content text",
                               is_anonymous=True,
                               is_content_sexual=False,
                               is_content_social=False,
                               hit_count=5,
                               positive_vote_count=3,
                               negative_vote_count=2,
                               created_by=self.user,
                               parent_topic=topic,
                               parent_board=board,
                               commented_at=timezone.now())

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 1

        Article.objects.create(title="example article",
                               content="example content",
                               content_text="example content text",
                               is_anonymous=True,
                               is_content_sexual=False,
                               is_content_social=False,
                               hit_count=5,
                               positive_vote_count=3,
                               negative_vote_count=2,
                               created_by=self.user,
                               parent_topic=topic,
                               parent_board=board,
                               commented_at=timezone.now())

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 2

        Article.objects.create(title="example article",
                               content="example content",
                               content_text="example content text",
                               is_anonymous=True,
                               is_content_sexual=False,
                               is_content_social=False,
                               hit_count=5,
                               positive_vote_count=3,
                               negative_vote_count=2,
                               created_by=self.user,
                               parent_topic=topic,
                               parent_board=board,
                               commented_at=timezone.now())

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 3

    # article 생성이 잘 되는지 확인하는 테스트
    def test_create(self):
        board = Board.objects.create(slug="board_example",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="보드입니다",
                                     en_description="This is board")

        topic = Topic.objects.create(slug="topic_example",
                                     ko_name="토픽1",
                                     en_name="topic1",
                                     ko_description="토픽입니다",
                                     en_description="This is topic",
                                     parent_board=board)

        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=False,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=5,
                                         positive_vote_count=3,
                                         negative_vote_count=2,
                                         created_by=self.user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at=timezone.now())

        a = self.http_request('get', 'articles')

        a1 = a.data.get('results')[0]

        assert a1.get('title') == article.title
        assert a1.get('content') == article.content
        assert a1.get('content_text') == article.content_text
        assert a1.get('is_anonymous') == article.is_anonymous
        assert a1.get('is_content_sexual') == article.is_content_sexual
        assert a1.get('is_content_social') == article.is_content_social
        assert a1.get('hit_count') == article.hit_count
        assert a1.get('positive_vote_count') == article.positive_vote_count
        assert a1.get('negative_vote_count') == article.negative_vote_count
        assert a1.get('created_by')['username'] == self.user.username
        assert a1.get('parent_topic')['ko_name'] == article.parent_topic.ko_name
        assert a1.get('parent_board')['ko_name'] == article.parent_board.ko_name

    # 익명의 글쓴이가 익명임을 확인하는 테스트
    def test_anonymous_writer(self):
        board = Board.objects.create(slug="board_example",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="보드입니다",
                                     en_description="This is board")

        topic = Topic.objects.create(slug="topic_example",
                                     ko_name="토픽1",
                                     en_name="topic1",
                                     ko_description="토픽입니다",
                                     en_description="This is topic",
                                     parent_board=board)

        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=True,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=5,
                                         positive_vote_count=3,
                                         negative_vote_count=2,
                                         created_by=self.user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at=timezone.now())

        a = self.http_request('get', 'articles')
        a1 = a.data.get('results')[0]
        assert a1.get('created_by') == '익명'

    # hit_count, positive/negative votes, comments_count가 잘 업데이트 되는지 테스트
    def test_update_numbers(self):
        board = Board.objects.create(slug="hi",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="한글설명",
                                     en_description="english testing")

        topic = Topic.objects.create(slug="hi",
                                     ko_name="한글이름",
                                     en_name="e",
                                     ko_description="한글설명",
                                     en_description="d",
                                     parent_board=board)

        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=True,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=0,
                                         positive_vote_count=0,
                                         negative_vote_count=0,
                                         created_by=self.user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at=timezone.now())

        a = self.http_request('get', 'articles').data.get('results')[0]

        # test update_hit_count

        # originally, hit_count 0
        assert a.get('hit_count') == 0

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

