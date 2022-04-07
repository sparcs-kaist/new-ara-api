import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from apps.core.models import Board, Article
from apps.core.models.board import BoardNameType
from apps.user.models import UserProfile
from tests.conftest import RequestSetting, TestCase


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
            name_type=BoardNameType.REGULAR,
            is_content_sexual=False,
            is_content_social=False,
            created_by=request.cls.authors[i % 4],
            parent_board=request.cls.board
        )
        request.cls.posts.append(new_article)


@pytest.fixture(scope='class')
def set_index(request):
    call_command('search_index', '--delete', '-f')
    call_command('search_index', '--create')


@pytest.mark.usefixtures('set_user_client', 'set_index', 'set_board', 'set_authors', 'set_posts')
class TestArticleSearch(TestCase, RequestSetting):
    def test_main_search(self):
        # `main_search` 필터를 검사합니다. 개수 assertion 숫자들의 의미는 set_posts를 참고하세요.

        def get_searched_article_number(q):
            return self.http_request(
                self.user,
                'get',
                'articles',
                querystring=f'main_search__contains={q}'
            ).data['num_items']

        wanted_min_proportion = 0.9

        queries = [
            ('AAAA', 34),
            ('BBBB', 20),
            ('CCCC', 15),
            ('테스트', 100),
            ('User2', 25),
        ]

        results = [
            (
                get_searched_article_number(query[0]),
                query[1]
            ) for query in queries
        ]

        for searched, expected in results:
            assert expected * wanted_min_proportion <= searched <= expected

