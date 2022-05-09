import sys
from datetime import timedelta
from unittest.mock import patch

import pytest

from django.utils import timezone
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Article, Board
from apps.core.models.board import BoardNameType
from apps.core.models.communication_article import CommunicationArticle, SchoolResponseStatus
from apps.core.serializers.communication_article import CommunicationArticleSerializer
from apps.user.models import UserProfile
from ara.settings import ANSWER_PERIOD

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
            group=UserProfile.UserGroup.COMMUNICATION_BOARD_ADMIN,
            sso_user_info={
                'kaist_info': '{\"ku_kname\": \"\\ud669\"}',
                'first_name': 'FirstName',
                'last_name': 'LastName'
            },
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
        is_school_communication=True,
        name_type=BoardNameType.REALNAME
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
        parent_board=request.cls.communication_board,
        name_type=BoardNameType.REALNAME
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

    def _confirm_communication_article(self, article, user):
        return self.http_request(user, 'put', f'communication_articles/{article.id}')

    def _add_admin_comment(self, article):
        comment_data = {
            'content': 'Comment made in factory',
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
            'name_type': BoardNameType.REALNAME
        }
        res = self.http_request(self.user, 'post', 'articles', article_data)

        article = Article.objects.get(id=res.data.get('id'))

        if status == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD:
            pass
        elif status == SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM:
            users_tuple = (self.user2, self.user3, self.user4)
            self._add_upvotes(article, users_tuple)
        elif status == SchoolResponseStatus.PREPARING_ANSWER:
            self._confirm_communication_article(article, self.school_admin)
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
        from_status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        to_status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        users_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, users_tuple)
        assert self._get_communication_article_status(article) == to_status

    # 0 -> 2
    def test_BEFORE_UPVOTE_THRESHOLD_to_PREPARING_ANSWER(self):
        from_status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        to_status = SchoolResponseStatus.PREPARING_ANSWER

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._confirm_communication_article(article, self.school_admin)
        assert self._get_communication_article_status(article) == to_status

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
        from_status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        to_status = SchoolResponseStatus.PREPARING_ANSWER

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._confirm_communication_article(article, self.school_admin)
        assert self._get_communication_article_status(article) == to_status

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

    # 2 -> 1 (관리자가 답변 준비 중일 때 좋아요 수가 다시 증가할 경우)
    def test_PREPARING_ANSWER_to_BEFORE_SCHOOL_CONFIRM(self):
        status = SchoolResponseStatus.PREPARING_ANSWER

        article = self._create_article_with_status(status)
        assert self._get_communication_article_status(article) == status

        # 좋아요 수가 threshold를 넘었을 때
        users_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, users_tuple)
        assert self._get_communication_article_status(article) == status

        # 좋아요 수가 threshold 밑으로 내려갔다가 다시 올라갈 때
        # 정책상 소통게시판에서 vote_cancel은 허용되지 않으나, 테스트 정확성을 위해 첨부함
        self.http_request(self.user4, 'post', f'articles/{article.id}/vote_cancel')
        self.http_request(self.user4, 'post', f'articles/{article.id}/vote_positive')
        assert self._get_communication_article_status(article) == status

    # 3 -> 1
    def test_ANSWER_DONE_to_BEFORE_SCHOOL_CONFIRM(self):
        status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(status)
        assert self._get_communication_article_status(article) == status

        users_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, users_tuple)
        assert self._get_communication_article_status(article) == status

    # 3 -> 2 (관리자가 답변 완료한 글에 다시 확인했습니다 요청을 보낸 경우)
    def test_ANSWER_DONE_to_PREPARING_ANSWER(self):
        status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(status)
        assert self._get_communication_article_status(article) == status

        self._confirm_communication_article(article, self.school_admin)
        assert self._get_communication_article_status(article) == status

    def test_days_left(self):
        status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        article = self._create_article_with_status(status)

        # days_left가 설정되기 전
        res = self.http_request(self.school_admin, 'get', f'communication_articles/{article.id}')
        assert res.data.get('days_left') == sys.maxsize

        user_tuple = (self.user2, self.user3, self.user4)
        self._add_upvotes(article, user_tuple)
        res = self.http_request(self.school_admin, 'get', f'communication_articles/{article.id}')
        assert res.data.get('days_left') == ANSWER_PERIOD

    def test_days_left_in_local_timezone(self):
        status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        article = self._create_article_with_status(status)

        today = timezone.localtime().replace(hour=23, minute=59, second=0)
        tomorrow = (timezone.localtime() + timedelta(days=1)).replace(hour=0, minute=1, second=0)

        # localtime 기준으로 오늘에서 내일로 넘어갈 때 D-day 변경되는지 확인
        with patch.object(timezone, 'localtime', return_value=today):
            res = self.http_request(self.school_admin, 'get', f'communication_articles/{article.id}')
            assert res.data.get('days_left') == ANSWER_PERIOD

        with patch.object(timezone, 'localtime', return_value=tomorrow):
            res = self.http_request(self.school_admin, 'get', f'communication_articles/{article.id}')
            assert res.data.get('days_left') == ANSWER_PERIOD - 1



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
        article_title = 'Anonymous article'
        article_data = {
            'title': article_title,
            'content': 'Content of anonymous article',
            'content_text': 'Content text of anonymous article',
            'created_by': self.user.id,
            'parent_board': self.communication_board.id,
            'name_type': BoardNameType.ANONYMOUS
        }
        res = self.http_request(self.user, 'post', 'articles', article_data).data
        assert res.get('name_type') == BoardNameType.REALNAME

    # 익명 댓글 작성 불가 확인
    def test_anonymous_comment(self):
        comment_data = {
            'content': 'Anonymous comment',
            'created_by': self.user.id,
            'parent_article': self.article.id,
            'name_type': BoardNameType.ANONYMOUS
        }
        res = self.http_request(self.user, 'post', 'comments', comment_data).data
        assert res.get('name_type') == BoardNameType.REALNAME

    # ======================================================================= #
    #                               Permission                                #
    # ======================================================================= #
    def test_admin_can_view_admin_api_list(self):
        res = self.http_request(self.school_admin, 'get', 'communication_articles')
        assert res.status_code == 200
        assert res.data.get('num_items') == CommunicationArticle.objects.all().count()

    def test_admin_can_view_admin_api_get(self):
        res = self.http_request(self.school_admin, 'get', f'communication_articles/{self.article.id}')
        assert res.status_code == 200
        assert res.data.get('article') == self.communication_article.article.id

    def test_admin_can_update_admin_api(self):
        res = self._confirm_communication_article(self.article, self.school_admin)
        assert res.status_code == 200
        self.communication_article.refresh_from_db()
        cas = CommunicationArticleSerializer(self.communication_article)
        assert res.data.get('confirmed_by_school_at') == cas.data['confirmed_by_school_at']

    def test_user_cannot_view_admin_api_list(self):
        res = self.http_request(self.user, 'get', 'communication_articles')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_view_admin_api_get(self):
        res = self.http_request(self.user, 'get', f'communication_articles/{self.article.id}')
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_user_cannot_update_admin_api(self):
        res = self._confirm_communication_article(self.article, self.user)
        assert res.status_code == status.HTTP_403_FORBIDDEN
