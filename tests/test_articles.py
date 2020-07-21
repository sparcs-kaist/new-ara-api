import pytest
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Vote, Article, ArticleReadLog, Topic, Board
from tests.conftest import RequestSetting


@pytest.mark.usefixtures('set_user_client')
class TestArticle(TestCase, RequestSetting):

    # Test number of articles in list
    def test_list(self):
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

        a = self.http_request('get', 'articles')
        assert a.data.get('num_items') == 0
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
        assert a.data.get('num_items') == 1
        article2 = Article.objects.create(title="example2",
                                          content="example content2",
                                          content_text="example content text 2",
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

        article3 = Article.objects.create(title="example3",
                                          content="example content3",
                                          content_text="example content text 3",
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

    def test_create(self):
        # writer = models.ForeignKey()
        board = Board.objects.create(slug="hi",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="testing",
                                     en_description="english testing")
        time = models.DateTimeField()
        topic = Topic.objects.create(slug = "hi",
                                     ko_name="k",
                                     en_name="e",
                                     ko_description="dd",
                                     en_description="d",
                                     parent_board=board)
        date_str="2020-05-22"
        temp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        user = get_user_model().objects.create_user(
            email='user1@gmail.com',
            username='user1',
            password='userpw1',
        )
        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=False,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=5,
                                         positive_vote_count=3,
                                         negative_vote_count=2,
                                         created_by=user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at = date_str,
                                         )

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
        assert a1.get('created_by')["username"] == 'user1'
        # assert a1.get('parent_topic') == article.parent_topic # This gives error
        # assert a1.get('parent_board') == article.parent_board # This gives error
        # assert a1.get('attachments') == article.attachments
        # assert a1.get('commented_at') == article.commented_at

    # Test if anonymous writer's article is anonymous
    def test_anonymous_writer(self):
        # writer = models.ForeignKey()
        board = Board.objects.create(slug="hi",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="testing",
                                     en_description="english testing")
        time = models.DateTimeField()
        topic = Topic.objects.create(slug = "hi",
                                     ko_name="k",
                                     en_name="e",
                                     ko_description="dd",
                                     en_description="d",
                                     parent_board=board)
        # naive = datetime(loc_year, loc_month, loc_date, loc_hour, loc_minute)
        date_str="2020-05-22"
        temp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        user = get_user_model().objects.create_user(
            email='jj',
            username='hi',
            password='pw',
        )
        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=True,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=5,
                                         positive_vote_count=3,
                                         negative_vote_count=2,
                                         created_by=user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at = date_str,
                                         )

        Comment.objects.create(content='Sample comment',
                               is_anonymous=True,
                               positive_vote_count=4,
                               negative_vote_count=3,
                               created_by=user,
                               # attachment=1,
                               parent_article=article,
                               # parent_comment=4,
                               )
        a = self.http_request('get', 'articles')
        a1 = a.data.get('results')[0]
        assert a1.get('created_by') == '익명'

    # test if article's viewcount, pos/neg votes, and number of comments are properly updated
    def test_update_numbers(self):
        # writer = models.ForeignKey()
        board = Board.objects.create(slug="hi",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="testing",
                                     en_description="english testing")
        time = models.DateTimeField()
        topic = Topic.objects.create(slug = "hi",
                                     ko_name="k",
                                     en_name="e",
                                     ko_description="dd",
                                     en_description="d",
                                     parent_board=board)
        # naive = datetime(loc_year, loc_month, loc_date, loc_hour, loc_minute)
        date_str="2020-05-22"
        temp_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        user = get_user_model().objects.create_user(
            email='jj',
            username='hi',
            password='pw',
        )
        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=True,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=0,
                                         positive_vote_count=0,
                                         negative_vote_count=0,
                                         created_by=user,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at = date_str,
                                       )

        a1 = self.http_request('get', 'articles').data.get('results')[0]

        # test update_hit_count
        article.update_hit_count()
        assert a1.get('hit_count') == 0
        voter1 = get_user_model().objects.create_user(
            email='vote1@gmail.com',
            username='voter1id',
            password='voter1pw',
        )
        article_read_log = ArticleReadLog.objects.create(read_by=voter1,
                                                         article=article)
        # article_read_log.last_read_at()
        #article_read_log.prefetch_my_article_read_log(voter1)
        article.update_hit_count()
        a1 = self.http_request('get', 'articles').data.get('results')[0]
        assert a1.get('hit_count') == 1

        # test update_vote_status
        assert a1.get('positive_vote_count') == 0
        assert a1.get('negative_vote_count') == 0

        vote1 = Vote.objects.create(is_positive=True,
                                    voted_by=voter1,
                                    parent_article=article)

        article.update_vote_status()

        a1 = self.http_request('get', 'articles').data.get('results')[0]
        assert a1.get('positive_vote_count') == 1
        assert a1.get('negative_vote_count') == 0

        voter2 = get_user_model().objects.create_user(
            email='vote2@gmail.com',
            username='voter2id',
            password='voter2pw',
        )

        vote2 = Vote.objects.create(is_positive=False,
                                    voted_by=voter2,
                                    parent_article=article)

        article.update_vote_status()

        a1 = self.http_request('get', 'articles').data.get('results')[0]
        assert a1.get('positive_vote_count') == 1
        assert a1.get('negative_vote_count') == 1

        # test comments_count
        assert article.comments_count == 0
        Comment.objects.create(content='Sample comment',
                               is_anonymous=True,
                               positive_vote_count=4,
                               negative_vote_count=3,
                               created_by=user,
                               # attachment=1,
                               parent_article=article,
                               # parent_comment=4,
                               )
        a1 = self.http_request('get', 'articles').data.get('results')[0]
        assert article.comments_count == 1

    # Test if article's contents (title, text, board etc.) are properly updated
    def test_update_article(self):
        # writer = models.ForeignKey()
        board = Board.objects.create(slug="hi",
                                     ko_name="게시판1",
                                     en_name="board1",
                                     ko_description="testing",
                                     en_description="english testing")
        topic = Topic.objects.create(slug = "hi",
                                     ko_name="k",
                                     en_name="e",
                                     ko_description="dd",
                                     en_description="d",
                                     parent_board=board)
        date_str="2020-05-22"
        user1 = get_user_model().objects.create_user(
            email='user1@gmail.com',
            username='user1name',
            password='user1pw',
        )
        user2 = get_user_model().objects.create_user(
            email='user2@gmail.com',
            username='user2name',
            password='user2pw',
        )
        article = Article.objects.create(title="example",
                                         content="example content",
                                         content_text="example content text",
                                         is_anonymous=True,
                                         is_content_sexual=False,
                                         is_content_social=False,
                                         hit_count=0,
                                         positive_vote_count=0,
                                         negative_vote_count=0,
                                         created_by=user1,
                                         parent_topic=topic,
                                         parent_board=board,
                                         commented_at = date_str,
                                       )

        assert self.http_request('get', 'articles').data.get('num_items') == 1

        # test: user other than writer tries to delete article
        ArticleDeleteLog.objects.create(deleted_by=user2,
                                        article=article
                                        )
        assert self.http_request('get', 'articles').data.get('num_items') == 1

        # test: writer tries to delete article
        ArticleDeleteLog.objects.create(deleted_by=user1,
                                        article=article
                                        )
        assert self.http_request('get', 'articles').data.get('num_items') == 0 # this fails. Why?



