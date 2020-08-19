import pytest
from django.contrib.auth.models import User
from django.test import TestCase

from apps.core.models import Board, Article
from apps.user.models import UserProfile
from tests.conftest import RequestSetting

# TODO: test_articles fixture와 중복되는 코드 합치기

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
def set_authors(request):
    # 사용자를 4명 추가합니다.
    request.cls.authors = []
    for i in range(4):
        new_user, _ = User.objects.get_or_create(username=f'User{i+1}', email=f'user{i+1}@sparcs.org')
        if not hasattr(new_user, 'profile'):
            UserProfile.objects.get_or_create(user=new_user, nickname=f'User{i+1}')
        request.cls.authors.append(new_user)


@pytest.fixture(scope='class')
def set_posts(request):
    """
    게시물 100개를 추가합니다. 게시물 제목, 작성자, 내용이 번호에 따라 달라집니다.
    `set_authors`, `set_board` 가 먼저 셋팅되어야 합니다.
    """
    request.cls.posts = []
    for i in range(100):
        article_content = f'테스트 게시물입니다. '
        if i % 3 == 0:
            article_content += 'AAAA'
        if i % 5 == 0:
            article_content += 'BBBB'
        if i % 7 == 0:
            article_content += 'CCCC'
        new_article = Article.objects.create(
            title=f'게시물 {i+1}',
            content=article_content,
            content_text=article_content,
            is_anonymous=False,
            is_content_sexual=False,
            is_content_social=False,
            created_by=request.cls.authors[i % 4],
            parent_board=request.cls.board
        )
        request.cls.posts.append(new_article)

@pytest.mark.usefixtures('set_user_client', 'set_board', 'set_authors', 'set_posts')
class TestArticleSearch(TestCase, RequestSetting):
    def test_title_or_content(self):
        # `title_or_content__contains` 필터를 검사합니다. 개수 assertion 숫자들의 의미는 set_posts를 참고하세요.
        response = self.http_request(self.user, 'get', 'articles', querystring='title_or_content__contains=AAAA')
        assert response.data['num_items'] == 34
        response = self.http_request(self.user, 'get', 'articles', querystring='title_or_content__contains=BBBB')
        assert response.data['num_items'] == 20
        response = self.http_request(self.user, 'get', 'articles', querystring='title_or_content__contains=CCCC')
        assert response.data['num_items'] == 15
        response = self.http_request(self.user, 'get', 'articles', querystring='title_or_content__contains=2')
        assert response.data['num_items'] == 19  # *2, 2*: 총 19개
        response = self.http_request(self.user, 'get', 'articles', querystring='title_or_content__contains=테스트')
        assert response.data['num_items'] == 100

    def test_main_search(self):
        for user in self.authors:
            print(user.profile.nickname)
        # `main_search` 필터를 검사합니다. 개수 assertion 숫자들의 의미는 set_posts를 참고하세요.
        response = self.http_request(self.user, 'get', 'articles', querystring='main_search__contains=AAAA')
        assert response.data['num_items'] == 34
        response = self.http_request(self.user, 'get', 'articles', querystring='main_search__contains=BBBB')
        assert response.data['num_items'] == 20
        response = self.http_request(self.user, 'get', 'articles', querystring='main_search__contains=CCCC')
        assert response.data['num_items'] == 15
        response = self.http_request(self.user, 'get', 'articles', querystring='main_search__contains=테스트')
        assert response.data['num_items'] == 100
        response = self.http_request(self.user, 'get', 'articles', querystring='main_search__contains=User2')
        assert response.data['num_items'] == 25
