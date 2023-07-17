import pytest

from apps.core.models import Article, Board, Comment, Notification, NotificationReadLog
from tests.conftest import RequestSetting, TestCase


@pytest.fixture(scope="class")
def set_board(request):
    request.cls.board = Board.objects.create(
        slug="free",
        ko_name="자유 게시판",
        en_name="Free Board",
    )


@pytest.fixture(scope="class")
def set_articles(request):
    """set_board 먼저 적용"""
    request.cls.article = Article.objects.create(
        title="테스트 글입니다.",
        content="테스트 내용입니다.",
        content_text="테스트 텍스트",
        parent_board=request.cls.board,
        created_by=request.cls.user,
    )


@pytest.fixture(scope="function")
def set_comment(request):
    """set_articles 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content="댓글입니다.",
        created_by=request.cls.user2,
        parent_article=request.cls.article,
    )


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_board", "set_articles", "set_comment"
)
class TestNotification(TestCase, RequestSetting):
    def test_notification_article_commented(self):
        notifications = self.http_request(self.user, "get", "notifications")

        # user에게 알림: user의 글에 user2가 댓글을 달아서
        assert notifications.status_code == 200
        assert (
            notifications.data.get("results")[0].get("related_article")["id"]
            == self.article.id
        )
        assert Notification.objects.all().count() == 1

        assert notifications.data.get("num_items") == 1

    def test_notification_comment_commented(self):
        cc = Comment.objects.create(
            content="대댓글입니다.", created_by=self.user, parent_comment=self.comment
        )

        notifications = self.http_request(self.user2, "get", "notifications")

        # user2에게 알림: user2의 댓글에 user가 대댓글을 달아서
        assert notifications.status_code == 200
        assert (
            notifications.data.get("results")[0].get("related_comment")["id"]
            == self.comment.id
        )
        assert Notification.objects.filter(related_comment=self.comment).count() == 1

        assert notifications.data.get("num_items") == 1


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_board", "set_articles"
)
class TestNotificationReadLog(TestCase, RequestSetting):
    @pytest.mark.usefixtures("set_comment")
    def test_read(self):
        notification = Notification.objects.get(related_article=self.article)
        notification_read = self.http_request(
            self.user, "post", f"notifications/{notification.id}/read"
        )

        assert notification_read.status_code == 200

        # check is_read is True
        notification_read_log = NotificationReadLog.objects.filter(
            read_by=self.user, notification=notification
        ).get()
        assert notification_read_log.is_read

    def test_read_all(self):
        Comment.objects.create(
            content="댓글입니다.", created_by=self.user2, parent_article=self.article
        )

        notification_read = self.http_request(
            self.user, "post", "notifications/read_all"
        )
        assert notification_read.status_code == 200

        notification_read_log = NotificationReadLog.objects.filter(read_by=self.user)

        # check is_read is True
        assert (
            notification_read_log.count()
            == notification_read_log.filter(is_read=True).count()
        )
