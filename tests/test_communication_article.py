import pytest

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework.test import APIClient

from apps.core.models import Article, Board, Comment
from apps.core.models.communication_article import CommunicationArticle, SchoolResponseStatus
from apps.user.models import UserProfile

from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope='class')
def set_school_admin(request):
    request.cls.school_admin, _ = User.objects.get_or_create(
        username='School Admin',
        email='schooladmin@sparcs.org'
    )
    if not hasattr(request.cls.school_admin, 'profile'):
        UserProfile.objects.get_or_create(
            user=request.cls.school_admin,
            nickname='School Admin',
            agree_terms_of_service_at=timezone.now(),
            is_school_admin=True
        )
    request.cls.api_client = APIClient()


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug='with-school',
        ko_name='학교와의 게시판 (테스트)',
        en_name='With School (Test)',
        ko_description='학교와의 게시판 (테스트)',
        en_description='With School (Test)',
        is_school_communication=True
    )


@pytest.fixture(scope='class')
def set_article(request):
    # After defining set_board
    request.cls.article = Article.objects.create(
        title='Article Title',
        content='Article Content',
        content_text='Article Content Text',
        created_by=request.cls.user,
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_article1(request):
    # After defining set_board
    request.cls.article1 = Article.objects.create(
        title='Article1 Title',
        content='Article1 Content',
        content_text='Article1 Content Text',
        created_by=request.cls.user,
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_article3(request):
    # After defining set_board
    request.cls.article3 = Article.objects.create(
        title='Article3 Title',
        content='Article3 Content',
        content_text='Article3 Content Text',
        created_by=request.cls.user,
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_communication_article(request):
    # After defining set_article
    request.cls.communication_article = CommunicationArticle.objects.create(
        article=request.cls.article
    )


@pytest.fixture(scope='class')
def set_communication_article1(request):
    # After defining set_article1
    request.cls.communication_article1 = CommunicationArticle.objects.create(
        article=request.cls.article1
    )


@pytest.fixture(scope='class')
def set_communication_article3(request):
    # After defining set_article3
    request.cls.communication_article3 = CommunicationArticle.objects.create(
        article=request.cls.article3
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_user_client3', 'set_user_client4',
                         'set_school_admin', 'set_board', 'set_article', 'set_article1', 'set_article3',
                         'set_communication_article', 'set_communication_article1', 'set_communication_article3')
class TestCommunicationArticle(TestCase, RequestSetting):
    # 소통 게시물이 communication_article 필드 가지는지 확인
    def test_article_has_communication_article(self):
        assert self.article.parent_board.is_school_communication is True
        assert hasattr(self.article, 'communication_article')
    
    # 필드 디폴트 값 확인
    def test_default_fields(self):
        min_time = timezone.datetime.min.replace(tzinfo=timezone.utc)
        assert all([
            self.communication_article.response_deadline == min_time,
            self.communication_article.confirmed_by_school_at == min_time,
            self.communication_article.answered_at == min_time
        ])

    # school_response_status 업데이트 확인
    def test_school_response_status(self):
        # vote 개수가 SCHOOL_RESPONSE_VOTE_THRESHOLD보다 작으면 status == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('communication_article_status') == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD

        # 게시물에 좋아요 3개 추가 (작성일 기준 SCHOOL_RESPONSE_VOTE_THRESHOLD == 3)
        users_tuple = (self.user2, self.user3, self.user4)
        for user in users_tuple:
            self.http_request(user, 'post', f'articles/{self.article.id}/vote_positive')

        # 좋아요 개수 업데이트 확인
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('positive_vote_count') == len(users_tuple)

        # 좋아요 개수가 SCHOOL_RESPONSE_VOTE_THRESHOLD 이상이므로 status == SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        assert res.get('communication_article_status') == SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM

        # response_deadline 업데이트 확인
        min_time = timezone.datetime.min.replace(tzinfo=timezone.utc)
        self.communication_article.refresh_from_db()
        assert self.communication_article.response_deadline != min_time

        # is_school_admin = True인 사용자가 코멘트 작성
        Comment.objects.create(
            content = 'School Official Comment',
            is_anonymous = False,
            created_by = self.school_admin,
            parent_article = self.article
        )

        # school admin이 코멘트 작성했으므로 status == SchoolResponseStatus.ANSWER_DONE
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('communication_article_status') == SchoolResponseStatus.ANSWER_DONE

        # answered_at 업데이트 확인
        self.communication_article.refresh_from_db()
        assert self.communication_article.answered_at != min_time

    # school_response_status가 단조 증가하는지 확인
    def test_school_response_only_increases(self):
        # status == 3  # SchoolResponseStatus.ANSWER_DONE
        Comment.objects.create(
            content = 'School Official Comment',
            is_anonymous = False,
            created_by = self.school_admin,
            parent_article = self.article
        )

        # article에 좋아요 3개 추가해서 status 업데이트 시도
        users_tuple = (self.user2, self.user3, self.user4)
        for user in users_tuple:
            self.http_request(user, 'post', f'articles/{self.article.id}/vote_positive')
        
        # status 변화 없는지 확인
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}').data
        assert res.get('communication_article_status') == SchoolResponseStatus.ANSWER_DONE
    
    # 좋아요 개수로 정렬 확인
    def test_ordering_by_positive_vote_count(self):
        # 게시물에 좋아요 추가
        # [ article : 2개 / article1 : 3개 / article3 : 1개 ]
        self.http_request(self.user2, 'post', f'articles/{self.article.id}/vote_positive')
        self.http_request(self.user3, 'post', f'articles/{self.article.id}/vote_positive')
        self.http_request(self.user2, 'post', f'articles/{self.article1.id}/vote_positive')
        self.http_request(self.user3, 'post', f'articles/{self.article1.id}/vote_positive')
        self.http_request(self.user4, 'post', f'articles/{self.article1.id}/vote_positive')
        self.http_request(self.user2, 'post', f'articles/{self.article3.id}/vote_positive')

        # positive_vote_count 오름차순
        filtered_res = self.http_request(self.user, 'get', 'communication_articles', querystring='ordering=article__positive_vote_count').data.get('results')
        filtered_mod = CommunicationArticle.objects.all().order_by('article__positive_vote_count')
        for fr, fm in zip(filtered_res, filtered_mod):
            assert fr['id'] == fm.id
        
        # positive_vote_count 내림차순
        filtered_res = self.http_request(self.user, 'get', 'communication_articles', querystring='ordering=-article__positive_vote_count').data.get('results')
        filtered_mod = CommunicationArticle.objects.all().order_by('-article__positive_vote_count')
        for fr, fm in zip(filtered_res, filtered_mod):
            assert fr['id'] == fm.id

    # 답변 진행 상황 필터링 확인
    def test_filtering_by_status(self):
        # article1 status == 1  # SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        self.http_request(self.user2, 'post', f'articles/{self.article1.id}/vote_positive')
        self.http_request(self.user3, 'post', f'articles/{self.article1.id}/vote_positive')
        self.http_request(self.user4, 'post', f'articles/{self.article1.id}/vote_positive')

        # article3 status == 3  # SchoolResponseStatus.ANSWER_DONE
        Comment.objects.create(
            content = 'School Official Comment',
            is_anonymous = False,
            created_by = self.school_admin,
            parent_article = self.article3
        )

        # Check filtering
        status_tuple = (
            SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD,
            SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM,
            SchoolResponseStatus.ANSWER_DONE
        )

        for status in status_tuple:
            querystring = f'school_response_status={status}'
            filtered_res = self.http_request(self.user, 'get', 'communication_articles', querystring=querystring).data.get('results')
            filtered_mod = CommunicationArticle.objects.filter(school_response_status=status)        
            assert len(filtered_res) == 1 and filtered_mod.count() == 1
            assert filtered_res[0]['school_response_status'] == filtered_mod.first().school_response_status
