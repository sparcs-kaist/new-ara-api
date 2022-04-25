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
def set_communication_board(request):
    request.cls.communication_board = Board.objects.create(
        slug='with-school',
        ko_name='학교와의 게시판 (테스트)',
        en_name='With School (Test)',
        ko_description='학교와의 게시판 (테스트)',
        en_description='With School (Test)',
        is_school_communication=True
    )


@pytest.fixture(scope='class')
def set_non_communication_board(request):
    request.cls.non_communication_board = Board.objects.create(
        slug='not with-school',
        ko_name='학교 아닌 게시판 (테스트)',
        en_name='Not With School (Test)',
        ko_description='학교 아닌 게시판 (테스트)',
        en_description='Not With School (Test)',
        is_school_communication=False
    )


@pytest.fixture(scope='class')
def set_article(request):
    # After defining set_communication_board
    request.cls.article = Article.objects.create(
        title='Communication Article Title',
        content='Communication Article Content',
        content_text='Communication Article Content Text',
        created_by=request.cls.user,
        parent_board=request.cls.communication_board
    )


@pytest.fixture(scope='class')
def set_communication_article(request):
    # After defining set_article
    request.cls.communication_article = CommunicationArticle.objects.create(
        article=request.cls.article
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_user_client3', 'set_user_client4',
                         'set_school_admin', 'set_communication_board', 'set_non_communication_board',
                         'set_article', 'set_communication_article')
class TestCommunicationArticle(TestCase, RequestSetting):

    # ======================================================================= #
    #                            Helper Functions                             #
    # ======================================================================= #

    def _get_communication_article_status(self, article):
        res = self.http_request(self.user, 'get', f'articles/{article.id}').data
        return res.get('communication_article_status')

    def _add_upvotes(self, article, users):
        for user in users:
            self.http_request(user, 'post', f'articles/{article.id}/vote_positive')
    
    def _add_admin_comment(self, article):
        comment_str = 'Comment made in factory'
        comment_data = {
            'content': comment_str,
            'created_by': self.school_admin.id,
            'parent_article': article.id
        }
        self.http_request(self.school_admin, 'post', 'comments', comment_data)

    # status를 가지는 communication_article 반환
    def _create_article_with_status(self, status=SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD):
        article_title = f'Factory: Article Status {status}'
        article_data = {
            'title': article_title,
            'content': 'Content made in factory',
            'content_text': 'Content Text made in factory',
            'created_by': self.user.id,
            'parent_board': self.communication_board.id,
        }
        self.http_request(self.user, 'post', 'articles', article_data)

        article = Article.objects.get(title=article_title)

        if status == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD:
            pass
        elif status == SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM:
            users_tuple = (self.user2, self.user3, self.user4)
            self._add_upvotes(article, users_tuple)
        elif status == SchoolResponseStatus.PREPARING_ANSWER:
            # 작성일 기준 status 변경 방법이 존재하지 않음
            article.communication_article.response_deadline = timezone.now()
            article.communication_article.confirmed_by_school_at = timezone.now()
            article.communication_article.school_response_status = SchoolResponseStatus.PREPARING_ANSWER
            article.communication_article.save()
        elif status == SchoolResponseStatus.ANSWER_DONE:
            self._add_admin_comment(article)
        
        return article

    # ======================================================================= #
    #                              Creation Test                              #
    # ======================================================================= #

    # communication_article 생성 확인
    def test_create_communication_article(self):
        # 소통 게시물 생성
        article_title = 'Article for test_create_communication_article'
        user_data = {
            'title': article_title,
            'content': 'Content for test_create_communication_article',
            'content_text': 'test_create_communication_article',
            'creted_by': self.user.id,
            'parent_board': self.communication_board.id
        }
        self.http_request(self.user, 'post', 'articles', user_data)

        article = Article.objects.get(title=article_title)

        # 소통 게시물이 생성될 때 communication_article이 함께 생성되는지 확인
        article_id = article.id
        communication_article = CommunicationArticle.objects.get(article_id=article_id)
        assert communication_article

        # 필드 default 값 확인
        min_time = timezone.datetime.min.replace(tzinfo=timezone.utc)
        assert all([
            communication_article.response_deadline == min_time,
            communication_article.confirmed_by_school_at == min_time,
            communication_article.answered_at == min_time,
            communication_article.school_response_status == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        ])
    
    # 소통 게시물이 아닌 게시물에 communication_article 없는지 확인
    def test_non_communication_article(self):
        # 비소통 게시물 생성
        article_title = 'Article for test_non_communication_article'
        user_data = {
            'title': article_title,
            'content': 'Content for test_non_communication_article',
            'content_text': 'test_non_communication_article',
            'creted_by': self.user.id,
            'parent_board': self.non_communication_board.id
        }
        self.http_request(self.user, 'post', 'articles', user_data)

        article_id = Article.objects.get(title=article_title).id
        communication_article = CommunicationArticle.objects.filter(article_id=article_id).first()
        assert communication_article is None

    # ======================================================================= #
    #                    SchoolResponseStatus Update Test                     #
    # ======================================================================= #

    # 0 -> 1
    def test_BEFORE_UPVOTE_THRESHOLD_to_BEFORE_SCHOOL_CONFIRM(self):
        from_stauts = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        to_status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM

        article = self._create_article_with_status(from_stauts)
        assert self._get_communication_article_status(article) == from_stauts

        users_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, users_tuple)
        assert self._get_communication_article_status(article) == to_status
    
    # 0 -> 2
    def test_BEFORE_UPVOTE_THRESHOLD_to_PREPARING_ANSWER(self):
        # TODO: '답변 준비 중' 버튼 제작 후 마저 작성
        pass

    # 0 -> 3
    def test_BEFORE_UPVOTE_THRESHOLD_to_ANSWER_DONE(self):
        from_status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        to_status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._add_admin_comment(article)
        assert self._get_communication_article_status(article) == to_status
    
    # 1 -> 2
    def test_BEFORE_SCHOOL_CONFIRM_to_PREPARING_ANSWER(self):
        # TODO: '답변 준비 중' 버튼 제작 후 마저 작성
        pass

    # 1 -> 3
    def test_BEFORE_SCHOOL_CONFIRM_to_ANSWER_DONE(self):
        from_status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        to_status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._add_admin_comment(article)
        assert self._get_communication_article_status(article) == to_status

    # 2 -> 3
    def test_PREPARING_ANSWER_to_ANSWER_DONE(self):
        from_status = SchoolResponseStatus.PREPARING_ANSWER
        to_status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._add_admin_comment(article)
        assert self._get_communication_article_status(article) == to_status
    
    # 2 -> 1 (관리자가 '답변 준비 중' 취소하는 경우)
    def test_PREPARING_ANSWER_to_BEFORE_SCHOOL_CONFIRM(self):
        # TODO: '답변 준비 중' 버튼 제작 후 마저 작성
        pass
    
    # 3 -> 1
    def test_ANSWER_DONE_to_BEFORE_SCHOOL_CONFIRM(self):
        status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(status)
        assert self._get_communication_article_status(article) == status

        users_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, users_tuple)
        assert self._get_communication_article_status(article) == status
    
    # 3 -> 2
    def test_ANSWER_DONE_to_PREPARING_ANSWER(self):
        # TODO: '답변 준비 중' 버튼 제작 후 마저 작성
        pass
    
    # ======================================================================= #
    #                          Ordering & Filtering                           #
    # ======================================================================= #
    
    # 좋아요 개수로 정렬 확인
    def test_ordering_by_positive_vote_count(self):
        # TODO: In different branch
        pass

    # 답변 진행 상황 필터링 확인
    def test_filtering_by_status(self):
        # TODO: In different branch
        pass

    # ======================================================================= #
    #                                Anonymous                                #
    # ======================================================================= #

    # 익명 게시물 작성 불가 확인
    def test_anonymous_article(self):
        pass

    # 익명 댓글 작성 불가 확인
    def test_anonymous_comment(self):
        pass
