import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.core.models import Article, Board, Topic
from apps.user import models
from apps.user.models import UserProfile
from tests.conftest import RequestSetting


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug="test board",
        ko_name="테스트 게시판",
        en_name="Test Board",
        ko_description="테스트 게시판입니다",
        en_description="This is a board for testing"
    )


@pytest.fixture(scope='class')
def set_articles(request):
    """set_board, set_topic 먼저 적용"""
    request.cls.user2, _ = User.objects.get_or_create(username='User2', email='user2@sparcs.org')
    common_kwargs = {
        'content': 'example content',
        'content_text': 'example content text',
        'is_anonymous': False,
        'created_by': request.cls.user2,
        'parent_board': request.cls.board,
        'hit_count': 0,
        'positive_vote_count': 0,
        'negative_vote_count': 0
        # Topic is nullable
    }
    request.cls.article_clean = Article.objects.create(
        title="클린한 게시물",
        is_content_sexual=False,
        is_content_social=False,
        commented_at=timezone.now(),
        **common_kwargs
    )
    request.cls.article_sexual = Article.objects.create(
        title='성인글',
        is_content_sexual=True,
        is_content_social=False,
        commented_at=timezone.now(),
        **common_kwargs
    )
    request.cls.article_social = Article.objects.create(
        title='정치글',
        is_content_sexual=False,
        is_content_social=True,
        **common_kwargs
    )
    request.cls.article_sexual_and_social = Article.objects.create(
        title='정치+성인글',
        is_content_sexual=True,
        is_content_social=True,
        **common_kwargs
    )


@pytest.mark.usefixtures('set_user_client_with_profile', 'set_board', 'set_articles')
class TestUser(TestCase, RequestSetting):
    def test_profile_edit(self):
        # 프로필 (ie. 사용자 설정)이 잘 변경되는지 확인합니다.
        res = self.http_request(self.user, 'get', f'user_profiles/{self.user.id}')
        assert res.status_code == 200
        assert res.data.get('see_sexual') == self.user.profile.see_sexual
        assert res.data.get('see_social') == self.user.profile.see_social
        assert res.data.get('nickname') == self.user.profile.nickname

        update_data = {'see_sexual': True, 'see_social': True}
        res = self.http_request(self.user, 'put', f'user_profiles/{self.user.id}', data=update_data)
        assert res.status_code == 200
        assert res.data.get('see_sexual') == self.user.profile.see_sexual
        assert res.data.get('see_social') == self.user.profile.see_social
        assert res.data.get('nickname') == self.user.profile.nickname


