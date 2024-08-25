from unittest.mock import patch

import pytest

from apps.core.models import Article, Board, Comment, Notification, NotificationReadLog
from apps.core.models.board import NameType
from ara.infra.notification.notification_infra import NotificationInfra
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
@pytest.mark.django_db
class TestNotificationInfra(TestCase, RequestSetting):
    @patch("ara.infra.notification.notification_infra.fcm_notify_comment")
    def test_create_notification_article_commented(self, mock_fcm_notify):
        Notification.objects.all().delete()
        NotificationReadLog.objects.all().delete()

        # 댓글 생성시 알림생성1
        self.comment = Comment.objects.create(
            content="새 댓글입니다.", created_by=self.user2, parent_article=self.article
        )

        notification_infra = NotificationInfra()
        # 알림추가2
        notification_infra.create_notification(self.comment)
        notifications = self.http_request(self.user, "get", "notifications")

        """
        print("All Notifications:")
        for notification in Notification.objects.all():
            print(f"ID: {notification.id}, Type: {notification.type}, Title: {notification.title}, Content: {notification.content}, Related Article: {notification.related_article.title if notification.related_article else 'None'}, Related Comment: {notification.related_comment.id if notification.related_comment else 'None'}")
            # Print user details for notifications
            read_logs = NotificationReadLog.objects.filter(notification=notification)
            for log in read_logs:
                user = log.read_by
                print(f"Notification sent to user: ID={user.id}, Username={user.username}, Email={user.email}")
        print("Article Name Type:", self.article.name_type)
        """

        assert notifications.status_code == 200
        assert notifications.data.get("num_items") == 2
        assert (
            notifications.data.get("results")[0].get("related_article")["id"]
            == self.article.id
        )
        assert Notification.objects.count() == 2

        mock_fcm_notify.assert_called_once()

    @patch("ara.infra.notification.notification_infra.fcm_notify_comment")
    def test_create_notification_comment_commented(self, mock_fcm_notify):
        Notification.objects.all().delete()
        NotificationReadLog.objects.all().delete()

        cc = Comment.objects.create(
            content="대댓글입니다.", created_by=self.user, parent_comment=self.comment
        )

        notification_infra = NotificationInfra()
        notification_infra.create_notification(cc)

        notifications = self.http_request(self.user2, "get", "notifications")

        print("Notifications Count:", Notification.objects.count())

        assert notifications.status_code == 200
        assert notifications.data.get("num_items") == 2
        assert (
            notifications.data.get("results")[0].get("related_comment")["id"]
            == self.comment.id
        )
        assert Notification.objects.filter(related_comment=self.comment).count() == 2

        # Verify that fcm_notify_comment was called
        mock_fcm_notify.assert_called_once()


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_board", "set_articles"
)


# testnotification read 로그도 테스트 케이스
@pytest.mark.django_db
class TestNotificationReadLog(TestCase, RequestSetting):
    @pytest.fixture(autouse=True)
    def setup(self):
        self.notification_infra = NotificationInfra()

    @pytest.mark.usefixtures("set_comment")
    def test_read(self):
        Notification.objects.all().delete()
        NotificationReadLog.objects.all().delete()

        self.notification_infra.create_notification(self.comment)
        notifications = Notification.objects.filter(related_article=self.article)

        assert notifications.count() == 1
        notification = notifications.get()

        self.notification_infra.read_all_notifications(self.user.id)

        notification_read_log = NotificationReadLog.objects.filter(
            read_by=self.user, notification=notification
        )

        print("Notification Read Log Count:", notification_read_log.count())

        assert notification_read_log.count() == 1
        assert notification_read_log.get().is_read

    def test_read_all(self):
        Notification.objects.all().delete()
        NotificationReadLog.objects.all().delete()

        Comment.objects.create(
            content="댓글입니다.", created_by=self.user2, parent_article=self.article
        )

        self.notification_infra.read_all_notifications(self.user.id)

        notification_read_log = NotificationReadLog.objects.filter(read_by=self.user)

        print("Notification Read Log Count:", notification_read_log.count())

        assert notification_read_log.count() == 1
        assert (
            notification_read_log.filter(is_read=True).count()
            == notification_read_log.count()
        )
