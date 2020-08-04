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
    """set_board, set_user_client2 먼저 적용"""
    common_kwargs = {
        'content': 'example content',
        'content_text': 'example content text',
        'is_anonymous': False,
        'created_by': request.cls.user2,
        'parent_board': request.cls.board,
        'hit_count': 0,
        # Topic is nullable
    }
    # 키: Article ID, 값: (성인글 여부, 정치글 여부,) 의 tuple
    # 글목록 테스트 때 빠른 lookup을 위해 사용합니다.
    request.cls.articles_meta = {}
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
    request.cls.articles_meta[request.cls.article_clean.id] = (False, False)
    request.cls.articles_meta[request.cls.article_sexual.id] = (True, False)
    request.cls.articles_meta[request.cls.article_social.id] = (False, True)
    request.cls.articles_meta[request.cls.article_sexual_and_social.id] = (True, True)


@pytest.mark.usefixtures('set_user_client_with_profile', 'set_user_client2', 'set_board', 'set_articles')
class TestUser(TestCase, RequestSetting):
    def test_profile_edit(self):
        # 프로필 (ie. 사용자 설정)이 잘 변경되는지 테스트합니다.
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

    def test_filter_articles_list(self):
        # 사용자의 게시물 필터에 따라 게시물 목록에서 필터링이 잘 되는지 테스트합니다.
        def single_case(see_sexual: bool, see_social: bool):
            self.user.profile.see_sexual = see_sexual
            self.user.profile.see_social = see_social
            self.user.profile.save()

            resp = self.http_request(self.user, 'get', 'articles', querystring=f'parent_board={self.board.id}').data
            # 목록에 fixture 에서 설정한 게시물만 들어가 있는지 확인
            for post in resp.get('results'):
                hidden = post.get('is_hidden')
                post_id = post.get('id')
                is_sexual, is_social = self.articles_meta[post_id]
                assert hidden == ((is_sexual and not see_sexual) or (is_social and not see_social))

        single_case(True, True)
        single_case(True, False)
        single_case(False, True)
        single_case(False, False)

    def test_filter_articles_read(self):
        # 사용자의 게시물 필터에 따라 게시물 조회에서 필터링이 잘 되는지 테스트합니다.
        def single_case(see_sexual: bool, see_social: bool):
            self.user.profile.see_sexual = see_sexual
            self.user.profile.see_social = see_social
            self.user.profile.save()

            for article_id, meta in self.articles_meta.items():
                resp = self.http_request(self.user, 'get', f'articles/{article_id}').data
                hidden = resp.get('is_hidden')
                is_sexual, is_social = meta
                assert hidden == ((is_sexual and not see_sexual) or (is_social and not see_social))

        single_case(True, True)
        single_case(True, False)
        single_case(False, True)
        single_case(False, False)

    def test_filter_articles_best(self):
        # 사용자의 게시물 필터에 따라 베스트 게시물 목록에서 필터링이 잘 되는지 테스트합니다.
        def single_case(see_sexual: bool, see_social: bool):
            self.user.profile.see_sexual = see_sexual
            self.user.profile.see_social = see_social
            self.user.profile.save()

            resp = self.http_request(
                self.user, 'get', 'articles/best', querystring=f'parent_board={self.board.id}').data
            for post in resp.get('results'):
                hidden = post.get('is_hidden')
                post_id = post.get('id')
                is_sexual, is_social = self.articles_meta[post_id]
                assert hidden == ((is_sexual and not see_sexual) or (is_social and not see_social))

        single_case(True, True)
        single_case(True, False)
        single_case(False, True)
        single_case(False, False)
