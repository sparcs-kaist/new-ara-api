import pytest
from django.db.models import signals
from django.utils import timezone
from rest_framework import status

from apps.core.models import Comment
from apps.core.models.board import NameType
from apps.core.models.signals.comment import comment_post_save_signal
from apps.user.models.fcm_token import FCMToken
from ara.fcm import fcm
from tests.conftest import RequestSetting, TestCase, Utils


@pytest.fixture(scope="class")
def set_user_fcm_token(request):
    request.cls.token = FCMToken.objects.create(
        token="fcm_token_test", user=request.cls.user, last_activated_at=timezone.now()
    )


@pytest.mark.usefixtures(
    "set_user_client",
    "set_user_client2",
    "set_user_client3",
    "set_user_fcm_token",
    "set_boards",
    "set_topics",
    "set_articles",
)
class TestFCM(TestCase, RequestSetting):
    def test_token_update(self):
        user = Utils.create_user(
            username="no_token_user",
            email="no_token_user@sparcs.org",
            nickname="no_token_user",
        )
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 0

        res = self.http_request(user, "patch", "fcm/token/update", {"token": "token"})
        assert res.status_code == status.HTTP_200_OK
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0].token == "token"

        res = self.http_request(user, "patch", "fcm/token/update", {"token": "token2"})
        assert res.status_code == status.HTTP_200_OK
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 2
        assert filtered_tokens[0].token == "token2"

    def test_token_delete_none(self):
        user = Utils.create_user(
            username="no_token_user",
            email="no_token_user@sparcs.org",
            nickname="no_token_user",
        )
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 0

        res = self.http_request(
            user, "patch", "fcm/token/delete", {"token": "none_token"}
        )
        assert res.status_code == status.HTTP_200_OK
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 0

    def test_token_delete(self):
        user = Utils.create_user(
            username="no_token_user",
            email="no_token_user@sparcs.org",
            nickname="no_token_user",
        )
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 0

        res = self.http_request(user, "patch", "fcm/token/update", {"token": "token"})
        assert res.status_code == status.HTTP_200_OK
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 1
        assert filtered_tokens[0].token == "token"

        res = self.http_request(user, "patch", "fcm/token/delete", {"token": "token"})
        assert res.status_code == status.HTTP_200_OK
        filtered_tokens = FCMToken.objects.filter(user=user)
        assert len(filtered_tokens) == 0

    def test_topic_subscribe(self):
        res = self.http_request(
            self.user, "patch", "fcm/topic", {"put": ["topic1", "topic2"], "delete": []}
        )
        assert res.status_code == status.HTTP_200_OK
        assert fcm.call_count("subscribe_to_topic") == 2
        res = self.http_request(self.user, "get", "fcm/topic")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 2

    def test_topic_unsubscribe(self):
        res = self.http_request(
            self.user, "patch", "fcm/topic", {"put": ["topic1", "topic2"], "delete": []}
        )

        res = self.http_request(
            self.user,
            "patch",
            "fcm/topic",
            {"put": ["topic3"], "delete": ["topic1", "unsubscribed_topic"]},
        )

        assert res.status_code == status.HTTP_200_OK
        assert fcm.call_count("unsubscribe_from_topic") == 2

        res = self.http_request(self.user, "get", "fcm/topic")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 2

    def test_board_notification(self):
        """
        게시판에 새로운 글이 올라오면 구독자들에게 웹 푸시 알림이 발송된다
        fcm_topic: board_{board.id}
        """
        fcm_topic = f"board_{self.board.id}"
        user_data = {
            "title": "article for test_create",
            "content": "content for test_create",
            "content_text": "content_text for test_create",
            "name_type": NameType.REGULAR.name,
            "is_content_sexual": False,
            "is_content_social": False,
            "parent_topic": self.topic.id,
            "parent_board": self.board.id,
        }

        prev_send_count = fcm.call_count("send")
        res = self.http_request(self.user, "post", "articles", user_data)
        assert res.status_code == status.HTTP_201_CREATED
        cur_send_count = fcm.call_count("send")
        assert prev_send_count + 1 == cur_send_count
        assert fcm.journal[-1]["name"] == "send"
        assert fcm.journal[-1]["params"]["topic"] == fcm_topic

    def test_post_notification(self):
        """
        게시글 내 새로운 댓글이 올라오면 구독자들에게 웹 푸시 알림이 발송된다
        fcm_topic: article_commented_{article.id}
        """
        fcm_topic = f"article_commented_{self.article.id}"

        prev_send_count = fcm.call_count("send")
        comment = Comment.objects.create(
            content="this is a test comment",
            name_type=NameType.REGULAR,
            created_by=self.user2,
            parent_article=self.article,
        )

        cur_send_count = fcm.call_count("send")
        assert prev_send_count + 2 == cur_send_count

        def is_sent_to_article_author(entry):
            return (
                entry["name"] == "send" and entry["params"]["token"] == self.token.token
            )

        def is_sent_to_subscribers(entry):
            return entry["name"] == "send" and entry["params"]["topic"] == fcm_topic

        assert any([is_sent_to_article_author(entry) for entry in fcm.journal[-2:]])
        assert any([is_sent_to_subscribers(entry) for entry in fcm.journal[-2:]])

    def test_reply(self):
        """
        댓글에 대댓글이 달리는 경우 구독자들에게 웹 푸시 알림이 발송된다
        fcm_topic: comment_commented_{comment.id}
        """
        comment1 = Comment.objects.create(
            content="this is a test comment",
            name_type=NameType.REGULAR,
            created_by=self.user,
            parent_article=self.article,
        )

        fcm_topic = f"comment_commented_{comment1.id}"

        prev_send_count = fcm.call_count("send")
        comment2 = Comment.objects.create(
            content="this is a test reply",
            name_type=NameType.REGULAR,
            created_by=self.user2,
            parent_comment=comment1,
        )

        cur_send_count = fcm.call_count("send")
        # send to 4: article author, article subscriber, comment1 author, comment1 subscriber
        assert prev_send_count + 4 == cur_send_count

        def is_sent_to_article_author(entry):
            return (
                entry["name"] == "send" and entry["params"]["token"] == self.token.token
            )

        def is_sent_to_subscribers(entry):
            return entry["name"] == "send" and entry["params"]["topic"] == fcm_topic

        assert any([is_sent_to_article_author(entry) for entry in fcm.journal[-2:]])
        assert any([is_sent_to_subscribers(entry) for entry in fcm.journal[-2:]])
