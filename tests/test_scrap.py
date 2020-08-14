import pytest
from django.test import TestCase
from tests.conftest import RequestSetting
from django.db.utils import IntegrityError

from apps.core.models import Scrap, Board, Article, Block
from apps.user.models import UserProfile


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug='free',
        ko_name='자유 게시판',
        en_name='Free Board',
        ko_description='자유 게시판 입니다.',
        en_description='This is a free board.'
    )


@pytest.fixture(scope='class')
def set_articles(request):
    """set_board 먼저 적용"""
    request.cls.article = Article.objects.create(
        title='테스트 글입니다.',
        content='테스트 내용입니다.',
        content_text='테스트 텍스트',
        parent_board=request.cls.board,
        created_by=request.cls.user
    )

    request.cls.article2 = Article.objects.create(
        title='테스트 글2입니다.',
        content='테스트 내용2입니다.',
        content_text='테스트 텍스트2',
        parent_board=request.cls.board,
        created_by=request.cls.user2
    )

    request.cls.article_sexual = Article.objects.create(
        title='테스트 성인글입니다.',
        content='테스트 성인글 내용입니다.',
        content_text='테스트 성인글 텍스트',
        parent_board=request.cls.board,
        created_by=request.cls.user2,
        is_content_sexual=True
    )

    request.cls.article_social = Article.objects.create(
        title='테스트 정치글입니다.',
        content='테스트 정치글 내용입니다.',
        content_text='테스트 정치글 텍스트',
        parent_board=request.cls.board,
        created_by=request.cls.user2,
        is_content_social=True
    )

@pytest.fixture(scope='function')
def set_block(request):
    request.cls.block = Block.objects.create(
        blocked_by=request.cls.user2,
        user=request.cls.user
    )


@pytest.mark.usefixtures('set_user_client_with_profile', 'set_user_client2', 'set_board', 'set_articles')
class TestScrap(TestCase, RequestSetting):
    def test_create(self):
        Scrap.objects.create(
            parent_article=self.article,
            scrapped_by=self.user
        )
        scrap = self.http_request(self.user, 'get', 'scraps')
        # user 게시글을 user이 scrap 했을 때
        assert scrap.data.get('num_items') == 1
        assert scrap.data.get('results')[0].get('scrapped_by')['username'] == self.user.username

        Scrap.objects.create(
            parent_article=self.article2,
            scrapped_by=self.user
        )
        scrap2 = self.http_request(self.user, 'get', 'scraps')
        # user, user2 게시글을 user이 scrap 했을 때
        assert scrap2.data.get('num_items') == 2

        Scrap.objects.create(
            parent_article=self.article,
            scrapped_by=self.user2
        )
        scrap3 = self.http_request(self.user2, 'get', 'scraps')
        # user 게시글을 user2가 scrap 했을 때
        assert scrap3.data.get('num_items') == 1
        assert scrap3.data.get('results')[0].get('scrapped_by')['username'] == self.user2.username

    def test_scrap_same_article(self):
        Scrap.objects.create(
            parent_article=self.article,
            scrapped_by=self.user
        )

        scrap = self.http_request(self.user, 'get', 'scraps')
        assert scrap.data.get('num_items') == 1

        # 같은 게시글 scrap -> db 에서 integrity error 발생
        try:
            Scrap.objects.create(
                parent_article=self.article,
                scrapped_by=self.user
            )

        except IntegrityError:
            assert True

        else:
            assert False

    def test_scrap_sexual(self):
        # 성인글에 대한 profile 설정 했을 때
        Scrap.objects.create(
            parent_article=self.article_sexual,
            scrapped_by=self.user
        )

        self.user.profile.see_sexual = True
        scrap = self.http_request(self.user, 'get', 'scraps')
        # 성인글 보도록 하면 scrap한 글이 보임
        assert scrap.data.get('num_items') == 1
        assert not scrap.data.get('results')[0].get('parent_article').get('is_hidden')

        self.user.profile.see_sexual = False
        scrap2 = self.http_request(self.user, 'get', 'scraps')
        # 성인글 안보도록 바꾸면 scrap한 글이 안보임
        assert scrap2.data.get('results')[0].get('parent_article').get('is_hidden')

    def test_scrap_social(self):
        # 정치글에 대한 profile 설정 했을 때
        Scrap.objects.create(
            parent_article=self.article_social,
            scrapped_by=self.user
        )

        self.user.profile.see_social = True
        scrap = self.http_request(self.user, 'get', 'scraps')

        # 정치글 보도록 하면 scrap한 글이 보임
        assert scrap.data.get('num_items') == 1
        assert not scrap.data.get('results')[0].get('parent_article').get('is_hidden')

        self.user.profile.see_social = False
        scrap2 = self.http_request(self.user, 'get', 'scraps')
        # 정치글 안보도록 바꾸면 scrap한 글이 안보임
        assert scrap2.data.get('results')[0].get('parent_article').get('is_hidden')

    @pytest.mark.usefixtures('set_block')
    def test_scrap_block(self):
        # user2가 user을 차단했을 때 user2가 user의 article을 scrap 하는 경우 안 보이는지 확인

        Scrap.objects.create(
            parent_article=self.article,
            scrapped_by=self.user2
        )

        scrap = self.http_request(self.user2, 'get', 'scraps')
        assert scrap.data.get('num_items') == 1
        assert scrap.data.get('results')[0].get('parent_article').get('is_hidden')

