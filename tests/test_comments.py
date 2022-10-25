from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import Article, Topic, Board, Comment, Block, Vote
from apps.core.models.board import BoardNameType
from apps.user.models import UserProfile
from ara.settings import MIN_TIME
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope="class")
def set_boards(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
        name_type=BoardNameType.REGULAR,
        ko_description="테스트 게시판입니다",
        en_description="This is a board for testing",
    )

    request.cls.realname_board = Board.objects.create(
        slug="test realname board",
        ko_name="테스트 실명 게시판",
        en_name="Test realname Board",
        name_type=BoardNameType.REALNAME,
        ko_description="테스트 실명 게시판입니다",
        en_description="This is a realname board for testing",
    )


@pytest.fixture(scope="class")
def set_topics(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug="test topic",
        ko_name="테스트 토픽",
        en_name="Test Topic",
        ko_description="테스트용 토픽입니다",
        en_description="This is topic for testing",
        parent_board=request.cls.board,
    )

    request.cls.realname_topic = Topic.objects.create(
        slug="test realname topic",
        ko_name="테스트 실명 토픽",
        en_name="Test realname Topic",
        ko_description="테스트용 실명 토픽입니다",
        en_description="This is realname topic for testing",
        parent_board=request.cls.realname_board,
    )


@pytest.fixture(scope="class")
def set_articles(request):
    """set_topic, set_user_client 먼저 적용"""
    request.cls.article_regular = Article.objects.create(
        title="Test Article",
        content="Content of test article",
        content_text="Content of test article in text",
        name_type=BoardNameType.REGULAR,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now(),
    )

    """set_topic, set_user_client 먼저 적용"""
    request.cls.article_anonymous = Article.objects.create(
        title="Anonymous Test Article",
        content="Content of test article",
        content_text="Content of test article in text",
        name_type=BoardNameType.ANONYMOUS,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now(),
    )

    """set_realname_topic, set_user_with_kaist_info 먼저 적용"""
    request.cls.realname_article = Article.objects.create(
        title="Realname Test Article",
        content="Content of test realname article",
        content_text="Content of test article in text",
        name_type=BoardNameType.REALNAME,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user_with_kaist_info,
        parent_topic=request.cls.realname_topic,
        parent_board=request.cls.realname_board,
        commented_at=timezone.now(),
    )

    """set_realname_topic, set_user_without_kaist_info 먼저 적용"""
    request.cls.realname_article_without_kinfo = Article.objects.create(
        title="Realname Test Article",
        content="Content of test realname article",
        content_text="Content of test article in text",
        name_type=BoardNameType.REALNAME,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user_without_kaist_info,
        parent_topic=request.cls.realname_topic,
        parent_board=request.cls.realname_board,
        commented_at=timezone.now(),
    )


@pytest.fixture(scope="class")
def set_comments(request):
    """set_article 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content="this is a test comment",
        name_type=BoardNameType.REGULAR,
        created_by=request.cls.user,
        parent_article=request.cls.article_regular,
    )

    request.cls.comment_anonymous = Comment.objects.create(
        content="this is an anonymous test comment",
        name_type=BoardNameType.ANONYMOUS,
        created_by=request.cls.user,
        parent_article=request.cls.article_anonymous,
    )

    request.cls.realname_comment = Comment.objects.create(
        content="this is an realname test comment",
        name_type=BoardNameType.REALNAME,
        created_by=request.cls.user_with_kaist_info,
        parent_article=request.cls.realname_article,
    )


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_client3",
    "set_user_client4",
    "set_user_with_kaist_info",
    "set_user_without_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
    "set_comments",
)
class TestComments(TestCase, RequestSetting):
    # comment 개수를 확인하는 테스트
    def test_comment_list(self):
        # number of comments is initially 0
        res = self.http_request(self.user, "get", f"articles/{self.article_regular.id}")
        assert res.data.get("comment_count") == 1

        comment2 = Comment.objects.create(
            content="Test comment 2",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_article=self.article_regular,
        )
        comment3 = Comment.objects.create(
            content="Test comment 3",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_article=self.article_regular,
        )

        res = self.http_request(self.user, "get", f"articles/{self.article_regular.id}")
        assert res.data.get("comment_count") == 3

    # post로 댓글 생성됨을 확인
    def test_create_comment(self):
        comment_str = "this is a test comment for test_create_comment"
        comment_data = {
            "content": comment_str,
            "parent_article": self.article_regular.id,
            "parent_comment": None,
            "attachment": None,
        }
        self.http_request(self.user, "post", "comments", comment_data)
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(content=comment_str)

    # post로 대댓글이 생성됨을 확인
    def test_create_subcomment(self):
        subcomment_str = "this is a test subcomment"
        subcomment_data = {
            "content": subcomment_str,
            "parent_comment": self.comment.id,
            "parent_article": None,
            "attachment": None,
        }
        self.http_request(self.user, "post", "comments", subcomment_data)
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(
            content=subcomment_str, parent_comment=self.comment.id
        )

    # 댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count(self):
        article = Article.objects.get(id=self.article_regular.id)
        assert article.comment_count == 1
        comment = Comment.objects.get(id=self.comment.id)
        comment.delete()
        article.refresh_from_db(fields=["comment_count"])
        assert article.comment_count == 0

    # 대댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count_with_subcomments(self):

        article = Article.objects.get(id=self.article_regular.id)
        print("comment set: ", article.comment_set)
        assert article.comment_count == 1

        subcomment1 = Comment.objects.create(
            content="Test comment 2",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_comment=self.comment,
        )

        article = Article.objects.get(id=self.article_regular.id)
        print("comment set: ", article.comment_set)
        assert article.comment_count == 2

        subcomment2 = Comment.objects.create(
            content="Test comment 3",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_comment=self.comment,
        )

        article = Article.objects.get(id=self.article_regular.id)
        print("comment set: ", article.comment_set)
        assert article.comment_count == 3

        # 대댓글 삭제
        comment = Comment.objects.get(id=subcomment2.id)
        comment.delete()
        article.refresh_from_db(fields=["comment_count"])
        assert article.comment_count == 2

    # get으로 comment가 잘 retrieve 되는지 확인
    def test_retrieve_comment(self):
        res = self.http_request(self.user, "get", f"comments/{self.comment.id}").data
        assert res.get("content") == self.comment.content
        assert res.get("parent_article") == self.comment.parent_article.id

    # 댓글 작성자가 자신의 댓글을 지울 수 있는지 확인
    def test_delete_comment_by_comment_writer(self):
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(id=self.comment.id)
        self.http_request(self.user, "delete", f"comments/{self.comment.id}")
        assert not Comment.objects.filter(deleted_at=MIN_TIME).filter(
            id=self.comment.id
        )

    # 다른 사용자의 댓글을 지울 수 없는 것 확인
    def test_delete_comment_by_not_comment_writer(self):
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(id=self.comment.id)
        self.http_request(self.user2, "delete", f"comments/{self.comment.id}")
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(id=self.comment.id)

    # 댓글을 삭제할 때, 그 댓글의 대댓글은 삭제되지 않는 것 확인
    def test_delete_comment_with_subcomment(self):
        subcomment = Comment.objects.create(
            content="Test subcomment",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_comment=self.comment,
        )
        comment = Comment.objects.filter(id=self.comment.id).get()
        # MetaDataModel class에서 delete하여 signal로 cascade 삭제 확인.
        comment.delete()
        assert Comment.objects.filter(deleted_at=MIN_TIME).filter(id=subcomment.id)

    # patch로 댓글을 수정할 수 있음을 확인
    def test_edit_comment_by_writer(self):
        edited_content = "this is an edited test comment"
        edited_comment_data = {
            "content": edited_content,
        }
        self.http_request(
            self.user, "patch", f"comments/{self.comment.id}", edited_comment_data
        )
        assert Comment.objects.get(id=self.comment.id).content == edited_content

    # 다른 사용자의 댓글을 수정할 수 없는 것 확인
    def test_edit_comment_by_nonwriter(self):
        original_content = self.comment.content
        edited_comment_data = {
            "content": "this is an edited test comment",
        }
        self.http_request(
            self.user2, "patch", f"comments/{self.comment.id}", edited_comment_data
        )
        assert Comment.objects.get(id=self.comment.id).content == original_content

    # http get으로 익명 댓글을 retrieve했을 때 작성자가 익명으로 나타나는지 확인
    def test_anonymous_comment(self):
        # 익명 댓글 생성
        anon_comment = Comment.objects.create(
            content="Anonymous test comment",
            name_type=BoardNameType.ANONYMOUS,
            created_by=self.user,
            parent_article=self.article_regular,
        )

        # 익명 댓글을 GET할 때, 작성자의 정보가 전달되지 않는 것 확인
        res = self.http_request(self.user, "get", f"comments/{anon_comment.id}").data
        assert res.get("name_type") == BoardNameType.ANONYMOUS
        assert res.get("created_by")["username"] != anon_comment.created_by.username

        res2 = self.http_request(self.user2, "get", f"comments/{anon_comment.id}").data
        assert res2.get("name_type") == BoardNameType.ANONYMOUS
        assert res2.get("created_by")["username"] != anon_comment.created_by.username

    # 익명글의 글쓴이가 본인의 글에 남긴 댓글에 대해, user_id가 같은지 확인
    def test_anonymous_comment_by_article_writer(self):
        # 익명 댓글 생성
        Comment.objects.create(
            content="Anonymous test comment",
            name_type=BoardNameType.ANONYMOUS,
            created_by=self.user,
            parent_article=self.article_anonymous,
        )

        r_article = self.http_request(
            self.user, "get", f"articles/{self.article_anonymous.id}"
        ).data
        article_writer_id = r_article.get("created_by")["id"]
        r_comment = self.http_request(
            self.user, "get", f"comments/{self.comment_anonymous.id}"
        ).data
        comment_writer_id = r_comment.get("created_by")["id"]
        assert article_writer_id == comment_writer_id

        r_article2 = self.http_request(
            self.user2, "get", f"articles/{self.article_anonymous.id}"
        ).data
        article_writer_id2 = r_article2.get("created_by")["id"]
        r_comment2 = self.http_request(
            self.user2, "get", f"comments/{self.comment_anonymous.id}"
        ).data
        comment_writer_id2 = r_comment2.get("created_by")["id"]
        assert article_writer_id2 == comment_writer_id2

    def test_comment_on_regular_parent_article(self):
        comment_data = {
            "content": "This is a comment on a regular parent article",
            "parent_article": self.article_regular.id,
            "parent_comment": None,
            "attachment": None,
        }
        res = self.http_request(self.user, "post", "comments", comment_data)

        assert res.data["name_type"] == BoardNameType.REGULAR
        assert Comment.objects.get(pk=res.data["id"]).name_type == BoardNameType.REGULAR

    def test_comment_on_regular_parent_comment(self):
        comment_str = "This is a comment on a regular parent comment"
        comment_data = {
            "content": comment_str,
            "parent_article": None,
            "parent_comment": self.comment.id,
            "attachment": None,
        }
        self.http_request(self.user, "post", "comments", comment_data)
        assert (
            Comment.objects.filter(content=comment_str).first().name_type
            == BoardNameType.REGULAR
        )

    def test_comment_on_anonymous_parent_article(self):
        comment_str = "This is a comment on an anonymous parent article"
        comment_data = {
            "content": comment_str,
            "parent_article": self.article_anonymous.id,
            "parent_comment": None,
            "attachment": None,
        }
        self.http_request(self.user, "post", "comments", comment_data)
        assert (
            Comment.objects.filter(content=comment_str).first().name_type
            == BoardNameType.ANONYMOUS
        )

    def test_comment_on_anonymous_parent_comment(self):
        comment_data = {
            "content": "This is a comment on an anonymous parent comment",
            "parent_article": None,
            "parent_comment": self.comment_anonymous.id,
            "attachment": None,
        }
        res = self.http_request(self.user, "post", "comments", comment_data)

        assert res.data["name_type"] == BoardNameType.ANONYMOUS
        assert (
            Comment.objects.get(pk=res.data["id"]).name_type == BoardNameType.ANONYMOUS
        )

    def test_comment_on_deleted_article(self):
        deleted_article = Article.objects.create(
            title="deleted article",
            content="deleted article content",
            content_text="deleted article content text",
            created_by=self.user,
            parent_board=self.board,
            deleted_at=timezone.now(),
        )
        res = self.http_request(
            self.user,
            "post",
            "comments",
            {
                "content": "deleted article comment content",
                "parent_article": deleted_article.id,
                "name_type": BoardNameType.REGULAR,
            },
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

    def test_comment_on_report_hidden_article(self):
        report_hidden_article = Article.objects.create(
            title="report hidden article",
            content="report hidden article content",
            content_text="report hidden article content text",
            created_by=self.user,
            parent_board=self.board,
            report_count=1_000_000,
            hidden_at=timezone.now(),
        )
        res = self.http_request(
            self.user,
            "post",
            "comments",
            {
                "content": "report hidden article comment content",
                "parent_article": report_hidden_article.id,
                "name_type": BoardNameType.REGULAR,
            },
        )
        assert res.status_code == status.HTTP_201_CREATED

    # 댓글 좋아요 확인
    def test_positive_vote(self):
        # 좋아요 2표
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_positive"
        )
        self.http_request(
            self.user3, "post", f"comments/{self.comment.id}/vote_positive"
        )

        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 2
        assert comment.negative_vote_count == 0

    # 댓글 싫어요 확인
    def test_negative_vote(self):
        # 싫어요 2표
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_negative"
        )
        self.http_request(
            self.user3, "post", f"comments/{self.comment.id}/vote_negative"
        )

        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 2

    # 투표 취소 후 재투표 가능한 것 확인
    def test_vote_undo_and_redo(self):
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_positive"
        )

        # 투표 취소
        self.http_request(self.user2, "post", f"comments/{self.comment.id}/vote_cancel")
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 0

        # 재투표
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_positive"
        )
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 1
        assert comment.negative_vote_count == 0

    # 댓글 중복 투표 안되는 것 확인. 중복투표시, 맨 마지막 투표 결과만 유효함
    def test_cannot_vote_both(self):
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_positive"
        )
        self.http_request(
            self.user2, "post", f"comments/{self.comment.id}/vote_negative"
        )
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 1


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_with_kaist_info",
    "set_user_without_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
    "set_comments",
)
class TestRealnameComments(TestCase, RequestSetting):
    def test_get_realname_comment(self):
        comment1 = Comment.objects.create(
            content="Realname test comment1",
            name_type=BoardNameType.REALNAME,
            created_by=self.user_without_kaist_info,
            parent_article=self.realname_article,
        )

        comment2 = Comment.objects.create(
            content="Realname test comment2",
            name_type=BoardNameType.REALNAME,
            created_by=self.user_with_kaist_info,
            parent_article=self.realname_article_without_kinfo,
        )

        res1 = self.http_request(
            self.user_without_kaist_info, "get", f"comments/{comment1.id}"
        ).data
        assert res1.get("name_type") == BoardNameType.REALNAME
        assert (
            res1.get("created_by")["username"] == comment1.created_by.profile.realname
        )

        res2 = self.http_request(
            self.user_with_kaist_info, "get", f"comments/{comment2.id}"
        ).data
        assert res2.get("name_type") == BoardNameType.REALNAME
        assert (
            res2.get("created_by")["username"] == comment2.created_by.profile.realname
        )

    def test_get_realname_comment_by_article_writer(self):
        res = self.http_request(
            self.user_with_kaist_info, "get", f"comments/{self.realname_comment.id}"
        ).data
        assert res.get("name_type") == BoardNameType.REALNAME
        assert res.get("created_by")["username"] == gettext("author")

    def test_create_realname_comment(self):
        comment_str = "This is a comment on a realname article"
        comment_data = {
            "content": comment_str,
            "parent_article": self.realname_article.id,
            "parent_comment": None,
            "attachment": None,
        }

        res = self.http_request(
            self.user_with_kaist_info, "post", "comments", comment_data
        ).data
        assert res.get("name_type") == BoardNameType.REALNAME
        assert (
            Comment.objects.get(content=comment_str).name_type == BoardNameType.REALNAME
        )

    def test_create_realname_subcomment(self):
        comment_str = "This is a subcomment on a realname comment"
        comment_data = {
            "content": comment_str,
            "parent_article": None,
            "parent_comment": self.realname_comment.id,
            "attachment": None,
        }

        res = self.http_request(
            self.user_with_kaist_info, "post", "comments", comment_data
        ).data
        assert res.get("name_type") == BoardNameType.REALNAME
        assert (
            Comment.objects.get(content=comment_str).name_type == BoardNameType.REALNAME
        )


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_with_kaist_info",
    "set_user_without_kaist_info",
    "set_boards",
    "set_topics",
    "set_articles",
    "set_comments",
)
class TestHiddenComments(TestCase, RequestSetting):
    def _comment_factory(self, **comment_kwargs):
        return Comment.objects.create(
            content="example comment",
            name_type=BoardNameType.REGULAR,
            created_by=self.user,
            parent_article=self.article_regular,
            **comment_kwargs,
        )

    def _test_can_override(self, user: User, target_comment: Comment, expected: bool):
        res = self.http_request(
            user, "get", f"comments/{target_comment.id}", None, "override_hidden"
        ).data
        assert res.get("hidden_content") is None
        assert res.get("why_hidden") is not None
        assert res.get("why_hidden") != []
        assert res.get("is_hidden") != expected
        if expected:
            assert res.get("content") is not None
        else:
            assert res.get("content") is None

    def test_blocked_user_block(self):
        Block.objects.create(blocked_by=self.user, user=self.user2)
        comment2 = Comment.objects.create(
            content="example comment",
            name_type=BoardNameType.REGULAR,
            created_by=self.user2,
            parent_article=self.article_regular,
        )

        res = self.http_request(self.user, "get", f"comments/{comment2.id}").data
        assert res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert "BLOCKED_USER_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.user, comment2, True)

    def _create_report_hidden_comment(self):
        return self._comment_factory(report_count=1000000, hidden_at=timezone.now())

    def _create_deleted_comment(self):
        return self._comment_factory(deleted_at=timezone.now())

    def test_reported_comment_block(self):
        target_comment = self._create_report_hidden_comment()

        res = self.http_request(self.user, "get", f"comments/{target_comment.id}").data
        assert not res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("content") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert "REPORTED_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.user, target_comment, False)

    def test_deleted_comment_block(self):
        target_comment = self._create_deleted_comment()

        res = self.http_request(self.user, "get", f"comments/{target_comment.id}").data
        assert not res.get("can_override_hidden")
        assert res.get("is_hidden")
        assert res.get("title") is None
        assert res.get("content") is None
        assert res.get("hidden_title") is None
        assert res.get("hidden_content") is None
        assert "DELETED_CONTENT" in res.get("why_hidden")
        self._test_can_override(self.user, target_comment, False)

    def test_block_reason_order(self):
        target_article = self._comment_factory(
            report_count=1000000,
            hidden_at=timezone.now(),
            deleted_at=timezone.now() + timedelta(days=1),
        )
        Block.objects.create(blocked_by=self.user2, user=self.user)

        res = self.http_request(self.user2, "get", f"comments/{target_article.id}").data
        assert res.get("is_hidden")
        assert res.get("why_hidden") == [
            "DELETED_CONTENT",
            "REPORTED_CONTENT",
            "BLOCKED_USER_CONTENT",
        ]

    def test_modify_deleted_comment(self):
        target_comment = self._create_deleted_comment()

        res = self.http_request(
            self.user,
            "patch",
            f"comments/{target_comment.id}",
            {
                "content": "attempt to modify deleted comment",
            },
        )

        assert res.status_code == 403

    def test_modify_report_hidden_comment(self):
        target_comment = self._create_report_hidden_comment()

        res = self.http_request(
            self.user,
            "patch",
            f"comments/{target_comment.id}",
            {"content": "attempt to modify hidden comment"},
        )
        assert res.status_code == 403

    def test_delete_already_deleted_comment(self):
        target_comment = self._create_deleted_comment()
        res = self.http_request(self.user, "delete", f"comments/{target_comment.id}")
        assert res.status_code == 403

    def test_delete_report_hidden_comment(self):
        target_comment = self._create_report_hidden_comment()
        res = self.http_request(self.user, "delete", f"comments/{target_comment.id}")
        assert res.status_code == 403

    def test_vote_deleted_comment(self):
        target_comment = self._create_deleted_comment()

        positive_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_positive"
        )
        assert positive_vote_result.status_code == 403

        negative_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_negative"
        )
        assert negative_vote_result.status_code == 403

        cancel_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_positive"
        )
        assert cancel_vote_result.status_code == 403

    def test_vote_report_hidden_article(self):
        target_comment = self._create_report_hidden_comment()

        positive_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_positive"
        )
        assert positive_vote_result.status_code == 403

        negative_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_negative"
        )
        assert negative_vote_result.status_code == 403

        Vote.objects.create(
            voted_by=self.user2,
            parent_comment=target_comment,
            is_positive=True,
        )
        target_comment.update_vote_status()

        cancel_vote_result = self.http_request(
            self.user2, "post", f"comments/{target_comment.id}/vote_positive"
        )
        assert cancel_vote_result.status_code == 403
        assert Comment.objects.get(id=target_comment.id).positive_vote_count == 1

    def test_report_deleted_article(self):
        target_comment = self._create_deleted_comment()

        res = self.http_request(
            self.user2,
            "post",
            "reports",
            {
                "content": "This is a report",
                "parent_article": target_comment.id,
                "parent_comment": None,
            },
        )

        assert res.status_code == 403

    def test_report_already_hidden_comment(self):
        target_comment = self._create_report_hidden_comment()

        res = self.http_request(
            self.user2,
            "post",
            "reports",
            {
                "content": "This is a report",
                "parent_article": target_comment.id,
                "parent_comment": None,
            },
        )

        assert res.status_code == 403

    def test_subcomment_on_deleted_comment(self):
        target_comment = self._create_deleted_comment()

        subcomment_str = "this is subcomment"
        res = self.http_request(
            self.user,
            "post",
            "comments",
            {
                "content": subcomment_str,
                "parent_article": None,
                "parent_comment": target_comment.id,
            },
        )

        assert res.status_code == 201
        assert Comment.objects.filter(
            content=subcomment_str, parent_comment=target_comment.id
        )

    def test_subcomment_on_report_hidden_comment(self):
        target_comment = self._create_report_hidden_comment()

        subcomment_str = "this is subcomment"
        res = self.http_request(
            self.user,
            "post",
            "comments",
            {
                "content": subcomment_str,
                "parent_article": None,
                "parent_comment": target_comment.id,
            },
        )

        assert res.status_code == 201
        assert Comment.objects.filter(
            content=subcomment_str, parent_comment=target_comment.id
        )
