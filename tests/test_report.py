import pytest
from apps.core.models import Article, Topic, Board, Comment, Report
from django.db.utils import IntegrityError
from tests.conftest import RequestSetting, TestCase
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
def set_article(request):
    """set_topic, set_user_client 먼저 적용"""
    request.cls.article = Article.objects.create(
        title='Test Article',
        content='Content of test article',
        content_text='Content of test article in text',
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


@pytest.fixture(scope='class')
def set_comment(request):
    """set_article 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content='this is a test comment',
        is_anonymous=False,
        created_by=request.cls.user,
        parent_article=request.cls.article,
    )


@pytest.fixture(scope='class')
def set_article_report(request):
    """set_article 먼저 적용 """
    request.cls.article_report = Report.objects.create(
        parent_article=request.cls.article,
        reported_by=request.cls.user,
        content='this is a test report for article'
    )


@pytest.fixture(scope='class')
def set_comment_report(request):
    """set_comment 먼저 적용 """
    request.cls.comment_report = Report.objects.create(
        parent_comment=request.cls.comment,
        reported_by=request.cls.user,
        content='this is a test report for comment'
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_user_client3', 'set_user_client4', 'set_board', 'set_topic', 'set_article', 'set_comment',
                         'set_article_report', 'set_comment_report')
class TestReport(TestCase, RequestSetting):
    # report 개수를 확인하는 테스트
    def test_report_list(self):
        res = self.http_request(self.user, 'get', 'reports')
        assert res.data.get('num_items') == 2

    # report list의 retrieve가 잘 되는지 확인
    def test_get_all_reports(self):
        res = self.http_request(self.user, 'get', 'reports').data
        report1 = res.get('results')[0]
        assert report1.get('id') == self.comment_report.id
        assert report1.get('parent_comment').get('id') == self.comment_report.parent_comment.id
        assert report1.get('reported_by').get('id') == self.comment_report.reported_by.id
        assert report1.get('content') == self.comment_report.content

        report2 = res.get('results')[1]
        assert report2.get('id') == self.article_report.id
        assert report2.get('parent_article').get('id') == self.article_report.parent_article.id
        assert report2.get('reported_by').get('id') == self.article_report.reported_by.id
        assert report2.get('content') == self.article_report.content

    # post로 리포트가 생성됨을 확인
    def test_create_report(self):
        # 게시글 신고
        report_str1 = 'this is an article report'
        report_data1 = {
            'content': report_str1,
            'parent_article': self.article.id,
        }
        response = self.http_request(self.user2, 'post', 'reports', report_data1)
        assert Report.objects.filter(content=report_str1)

        # 댓글 신고
        report_str2 = 'this is a comment report'
        report_data2 = {
            'content': report_str2,
            'parent_comment': self.comment.id,
        }
        self.http_request(self.user2, 'post', 'reports', report_data2)
        assert Report.objects.filter(content=report_str2)

    # 한 사용자가 같은 글/댓글에 대해 여러번 신고할 수 없음
    def test_cannot_repeat_report(self):
        try:
            Report.objects.create(
                parent_article=self.article,
                reported_by=self.user,
                content='this is another test report for article'
            )
        except IntegrityError:
            assert True
        else:
            assert False

    # 한 게시글이 여러번 신고당하면 자동 숨김되는 것 확인
    def test_hide_article_if_many_reports(self):
        # 신고가 1개 있는 상태에서는 article title, content가 잘 조회되는 것 확인
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('title') == self.article.title
        assert res.get('content') == self.article.content

        # 신고 2번 추가
        Report.objects.create(
            parent_article=self.article,
            reported_by=self.user2,
            content='test report 2'
        )

        Report.objects.create(
            parent_article=self.article,
            reported_by=self.user3,
            content='test report 3'
        )
        Report.objects.create(
            parent_article=self.article,
            reported_by=self.user4,
            content='test report 4'
        )

        # 신고가 threshold 이상인 경우 읽을 수 없음 (현재 총 4번 신고됨, 현재 threshold 4)
        res2 = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res2.get('title') != self.article.title
        assert res2.get('content') != self.article.content
        assert res2.get('title') is None
        assert res2.get('content') is None

    # 한 댓글이 여러번 신고당하면 자동 숨김되는 것 확인
    def test_hide_comment_if_many_reports(self):
        # 신고가 1개 있는 상태에서는 comment의 content가 잘 조회되는 것 확인
        res = self.http_request(self.user, 'get', f'comments/{self.comment.id}').data
        assert res.get('content') == self.comment.content

        # 신고 2번 추가
        Report.objects.create(
            parent_comment=self.comment,
            reported_by=self.user2,
            content='test report 2'
        )

        Report.objects.create(
            parent_comment=self.comment,
            reported_by=self.user3,
            content='test report 3'
        )

        Report.objects.create(
            parent_comment=self.comment,
            reported_by=self.user4,
            content='test report 4'
        )

        # 신고가 threshold 이상인 경우 읽을 수 없음 (현재 총 4번 신고됨, 현재 threshold 4)
        res2 = self.http_request(self.user, 'get', f'comments/{self.comment.id}').data
        assert res2.get('content') != self.comment.content
        assert res2.get('content') is None

