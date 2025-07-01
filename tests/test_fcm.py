from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import Board, Article
from apps.user.models import FCMToken
from tests.conftest import TestCase, RequestSetting


@pytest.fixture(scope="class")
def set_board(request):
    request.cls.board = Board.objects.create(
        slug="free",
        ko_name="자유 게시판",
        en_name="Free Board",
        ko_description="자유 게시판 입니다.",
        en_description="This is a free board.",
    )

@pytest.fixture(scope="class")
def set_articles(request):
    """set_board 먼저 적용"""
    request.cls.article = Article.objects.create(
        title="테스트 글입니다.",
        content="테스트 내용입니다.",
        content_text="테스트 텍스트",
        parent_board=request.cls.board,
        created_by=request.cls.user2,
    )

@pytest.fixture(scope="class")
def set_unexpired_mock_fcmtoken(request):
    print(f"now: {timezone.now()}")
    request.cls.fcm = FCMToken.objects.create(
        token="token",
        user=request.cls.user2,
        last_activated_at=timezone.now(),
        is_web=True
    )

@pytest.fixture(scope="class")
def set_expired_mock_fcmtoken(request):
    week_ago = timezone.now().date() - timedelta(days=7)
    
    request.cls.fcm_expired = FCMToken.objects.create(
        token="expired_token",
        user=request.cls.user2,
        last_activated_at=week_ago,
        is_web=True
    )

@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_board", "set_articles", "set_unexpired_mock_fcmtoken", "set_expired_mock_fcmtoken"
)
class TestFCMToken(TestCase, RequestSetting):
    def test_expire_token_on_request(self):
        # 유효하지 않은 토큰은 요청 발생 시 삭제
        tokens = FCMToken.objects.filter(user=self.user2)
        assert(len(tokens) == 2)

        comment_str = "this is a test comment for test_expire_token_on_request"
        comment_data = {
            "content": comment_str,
            "parent_article": self.article.id,
            "parent_comment": None,
            "attachment": None,
        }

        self.http_request(self.user, "post", "comments", comment_data)

        filtered_tokens = FCMToken.objects.filter(user=self.user2)
        assert(len(filtered_tokens) == 1)
