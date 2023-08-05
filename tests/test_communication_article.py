import sys
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from apps.core.models import Article, Board
from apps.core.models.board import NameType
from apps.core.models.communication_article import (
    CommunicationArticle,
    SchoolResponseStatus,
)
from apps.user.models import UserProfile
from ara.settings import ANSWER_PERIOD, MIN_TIME, SCHOOL_RESPONSE_VOTE_THRESHOLD

from .conftest import RequestSetting, TestCase, Utils


@pytest.fixture(scope="class")
def set_communication_board(request):
    request.cls.communication_board = Board.objects.create(
        slug="with-school",
        ko_name="학교와의 게시판 (테스트)",
        en_name="With School (Test)",
        is_school_communication=True,
        name_type=NameType.REALNAME,
        read_access_mask=0b11011110,
        write_access_mask=0b11011010,
    )


@pytest.fixture(scope="class")
def set_non_communication_board(request):
    request.cls.non_communication_board = Board.objects.create(
        slug="not with-school",
        ko_name="학교 아닌 게시판 (테스트)",
        en_name="Not With School (Test)",
        is_school_communication=False,
    )


@pytest.fixture(scope="class")
def set_article(request):
    # After defining set_communication_board
    request.cls.article = Article.objects.create(
        title="Communication Article Title",
        content="Communication Article Content",
        content_text="Communication Article Content Text",
        created_by=request.cls.user,
        parent_board=request.cls.communication_board,
        name_type=NameType.REALNAME,
    )


@pytest.fixture(scope="class")
def set_communication_article(request):
    # After defining set_article
    request.cls.communication_article = CommunicationArticle.objects.create(
        article=request.cls.article
    )


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_client3",
    "set_user_client4",
    "set_school_admin",
    "set_communication_board",
    "set_non_communication_board",
    "set_article",
    "set_communication_article",
)
class TestCommunicationArticle(TestCase, RequestSetting):
    # ======================================================================= #
    #                            Helper Functions                             #
    # ======================================================================= #

    def _get_communication_article_status(self, article):
        res = self.http_request(self.user, "get", f"articles/{article.id}")
        return res.data.get("communication_article_status")

    def _add_positive_votes(self, article, num):
        dummy_users = Utils.create_users(num)
        for user in dummy_users:
            self.http_request(user, "post", f"articles/{article.id}/vote_positive")

    def _add_admin_comment(self, article):
        comment_data = {
            "content": "Comment made in factory",
            "created_by": self.school_admin.id,
            "parent_article": article.id,
        }
        res = self.http_request(self.school_admin, "post", "comments", comment_data)
        assert res.data.get("created_by").get("profile").get("is_school_admin")

    # status를 가지는 communication_article 반환
    def _create_article_with_status(
        self, status=SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
    ):
        article_title = f"Factory: Article Status {status} created at {timezone.now()}"
        article_data = {
            "title": article_title,
            "content": "Content made in factory",
            "content_text": "Content Text made in factory",
            "created_by": self.user.id,
            "parent_board": self.communication_board.id,
            "name_type": NameType.REALNAME.name,
        }
        res = self.http_request(self.user, "post", "articles", article_data)

        article = Article.objects.get(pk=res.data.get("id"))

        if status == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD:
            pass
        elif status == SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM:
            self._add_positive_votes(article, SCHOOL_RESPONSE_VOTE_THRESHOLD)
        elif status == SchoolResponseStatus.ANSWER_DONE:
            self._add_admin_comment(article)

        return article

    # ======================================================================= #
    #                              Creation Test                              #
    # ======================================================================= #

    # communication_article 생성 확인
    def test_create_communication_article(self):
        # 소통 게시물 생성
        article_title = "Article for test_create_communication_article"
        user_data = {
            "title": article_title,
            "content": "Content for test_create_communication_article",
            "content_text": "test_create_communication_article",
            "creted_by": self.user.id,
            "parent_board": self.communication_board.id,
            "name_type": NameType.REALNAME.name,
        }
        self.http_request(self.user, "post", "articles", user_data)

        article = Article.objects.get(title=article_title)

        # 소통 게시물이 생성될 때 communication_article이 함께 생성되는지 확인
        article_id = article.id
        communication_article = CommunicationArticle.objects.get(article_id=article_id)
        assert communication_article

        # 필드 default 값 확인
        min_time = MIN_TIME
        assert all(
            [
                communication_article.response_deadline == min_time,
                communication_article.answered_at == min_time,
                communication_article.school_response_status
                == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD,
            ]
        )

    # 소통 게시물이 아닌 게시물에 communication_article 없는지 확인
    def test_non_communication_article(self):
        # 비소통 게시물 생성
        article_title = "Article for test_non_communication_article"
        user_data = {
            "title": article_title,
            "content": "Content for test_non_communication_article",
            "content_text": "test_non_communication_article",
            "creted_by": self.user.id,
            "parent_board": self.non_communication_board.id,
            "name_type": NameType.REGULAR.name,
        }
        self.http_request(self.user, "post", "articles", user_data)

        article_id = Article.objects.get(title=article_title).id
        communication_article = CommunicationArticle.objects.filter(
            article_id=article_id
        ).first()
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

        self._add_positive_votes(article, SCHOOL_RESPONSE_VOTE_THRESHOLD)
        assert self._get_communication_article_status(article) == to_status

    # 0 -> 2
    def test_BEFORE_UPVOTE_THRESHOLD_to_ANSWER_DONE(self):
        from_status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        to_status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._add_admin_comment(article)
        assert self._get_communication_article_status(article) == to_status

    # 1 -> 2
    def test_BEFORE_SCHOOL_CONFIRM_to_ANSWER_DONE(self):
        from_status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        to_status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(from_status)
        assert self._get_communication_article_status(article) == from_status

        self._add_admin_comment(article)
        assert self._get_communication_article_status(article) == to_status

    # 2 -> 1
    def test_ANSWER_DONE_to_BEFORE_SCHOOL_CONFIRM(self):
        status = SchoolResponseStatus.ANSWER_DONE

        article = self._create_article_with_status(status)
        assert self._get_communication_article_status(article) == status

        self._add_positive_votes(article, SCHOOL_RESPONSE_VOTE_THRESHOLD)
        assert self._get_communication_article_status(article) == status

    def test_days_left(self):
        status = SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        article = self._create_article_with_status(status)

        # days_left가 설정되기 전
        res = self.http_request(self.school_admin, "get", f"articles/{article.id}")
        assert res.data.get("days_left") == sys.maxsize
        #
        self._add_positive_votes(article, SCHOOL_RESPONSE_VOTE_THRESHOLD)
        res = self.http_request(self.school_admin, "get", f"articles/{article.id}")
        assert res.data.get("days_left") == ANSWER_PERIOD

    def test_days_left_in_local_timezone(self):
        status = SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
        article = self._create_article_with_status(status)

        today = timezone.localtime().replace(hour=23, minute=59, second=0)
        tomorrow = (timezone.localtime() + timedelta(days=1)).replace(
            hour=0, minute=1, second=0
        )

        # localtime 기준으로 오늘에서 내일로 넘어갈 때 D-day 변경되는지 확인
        with patch.object(timezone, "localtime", return_value=today):
            res = self.http_request(self.school_admin, "get", f"articles/{article.id}")
            assert res.data.get("days_left") == ANSWER_PERIOD

        with patch.object(timezone, "localtime", return_value=tomorrow):
            res = self.http_request(self.school_admin, "get", f"articles/{article.id}")
            assert res.data.get("days_left") == ANSWER_PERIOD - 1

    # ======================================================================= #
    #                          Ordering & Filtering                           #
    # ======================================================================= #

    # 좋아요 개수 내림차순 정렬 확인
    def test_descending_ordering_by_positive_vote_count(self):
        vote_counts = (0, 1, 2, 2, 3, 4)
        articles = [self._create_article_with_status() for _ in vote_counts]

        for vote_cnt, article in zip(vote_counts, articles):
            self._add_positive_votes(article, vote_cnt)

        res = self.http_request(
            self.user,
            "get",
            "articles",
            querystring="ordering=-positive_vote_count,-created_at",
        )
        assert res.status_code == HTTP_200_OK

        res_result = res.data.get("results")

        # 좋아요 개수 내림차순 정렬 확인
        res_positive_votes = [el.get("positive_vote_count") for el in res_result]
        assert res_positive_votes == sorted(res_positive_votes, reverse=True)

        # 좋아요 개수 같은 경우 최신 글이 앞에 있는지 확인
        res_vote_cnt_eq = [
            el.get("created_at")
            for el in res_result
            if el.get("positive_vote_count") == 2
        ]
        assert res_vote_cnt_eq == sorted(
            res_vote_cnt_eq,
            reverse=True,
            key=lambda date_str: datetime.fromisoformat(date_str),
        )

    # 좋아요 개수 오름차순 정렬 확인
    def test_ascending_ordering_by_positive_vote_count(self):
        vote_counts = (4, 3, 2, 2, 1, 0)
        articles = [self._create_article_with_status() for _ in vote_counts]

        for vote_cnt, article in zip(vote_counts, articles):
            self._add_positive_votes(article, vote_cnt)

        res = self.http_request(
            self.user,
            "get",
            "articles",
            querystring="ordering=positive_vote_count,-created_at",
        )
        assert res.status_code == HTTP_200_OK

        res_result = res.data.get("results")
        assert Article.objects.count() == len(res_result)

        # 좋아요 개수 오름차순 정렬 확인
        res_positive_votes = [el.get("positive_vote_count") for el in res_result]
        assert res_positive_votes == sorted(res_positive_votes)

        # 좋아요 개수 같은 경우 최신 글이 앞에 있는지 확인
        res_vote_cnt_eq = [
            el.get("created_at")
            for el in res_result
            if el.get("positive_vote_count") == 2
        ]
        assert res_vote_cnt_eq == sorted(
            res_vote_cnt_eq,
            reverse=True,
            key=lambda date_str: datetime.fromisoformat(date_str),
        )

    # 답변 진행 상황 필터링 확인
    def test_filtering_by_status(self):
        # 모든 status의 article 하나씩 생성
        for status in SchoolResponseStatus:
            self._create_article_with_status(status)

        # 답변 완료(status=3)
        res = self.http_request(
            self.user,
            "get",
            "articles",
            querystring=f"communication_article__school_response_status={SchoolResponseStatus.ANSWER_DONE}",
        )
        assert res.status_code == HTTP_200_OK
        res_status_set = {
            el.get("communication_article_status") for el in res.data.get("results")
        }
        assert res_status_set == {SchoolResponseStatus.ANSWER_DONE}

        # 답변 전(status<3)
        res = self.http_request(
            self.user,
            "get",
            "articles",
            querystring=f"communication_article__school_response_status__lt={SchoolResponseStatus.ANSWER_DONE}",
        )
        assert res.status_code == HTTP_200_OK
        res_status_set = {
            el.get("communication_article_status") for el in res.data.get("results")
        }
        assert res_status_set == {*SchoolResponseStatus} - {
            SchoolResponseStatus.ANSWER_DONE
        }

    # ======================================================================= #
    #                                Anonymous                                #
    # ======================================================================= #

    # 익명 게시물 작성 불가 확인
    def test_anonymous_article(self):
        article_title = "Anonymous article"
        article_data = {
            "title": article_title,
            "content": "Content of anonymous article",
            "content_text": "Content text of anonymous article",
            "created_by": self.user.id,
            "parent_board": self.communication_board.id,
            "name_type": NameType.ANONYMOUS.name,
        }
        result = self.http_request(self.user, "post", "articles", article_data)
        assert result.status_code == HTTP_400_BAD_REQUEST

    # 익명 댓글 작성 불가 확인
    def test_anonymous_comment(self):
        comment_data = {
            "content": "Anonymous comment",
            "created_by": self.user.id,
            "parent_article": self.article.id,
            "name_type": NameType.ANONYMOUS,
        }
        res = self.http_request(self.user, "post", "comments", comment_data).data
        assert res.get("name_type") == NameType.REALNAME

    # ======================================================================= #
    #                               School Admin                              #
    # ======================================================================= #

    # school_admin이 작성할 때 my_comment_profile REGULAR 확인
    def test_school_admin_my_comment_profile(self):
        res = self.http_request(
            self.school_admin, "get", f"articles/{self.article.id}"
        ).data

        assert res.get("my_comment_profile")["profile"]["is_school_admin"]
        assert (
            res.get("my_comment_profile")["profile"]["nickname"]
            == UserProfile.objects.get(user_id=self.school_admin.id).nickname
        )
