import pytest
from django.db import IntegrityError, transaction
from tests.conftest import RequestSetting, TestCase
from apps.core.models import Scrap, Board, Article, Block


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


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_articles')
class TestScrap(TestCase, RequestSetting):
    def test_create(self):
        scrap_data = {
            'parent_article': self.article.id
        }
        self.http_request(self.user, 'post', 'scraps', scrap_data)

        scrap = Scrap.objects.filter(parent_article=self.article, scrapped_by=self.user).get()
        assert scrap.scrapped_by == self.user and scrap.parent_article == self.article

    def test_wrong_create(self):
        scrap_data = {
            'parent_article': self.article.id + 100
        }
        response = self.http_request(self.user, 'post', 'scraps', scrap_data)
        # 존재하지 않는 게시물에 대한 request 요청
        assert response.status_code == 400

        scrap_data2 = {}
        response2 = self.http_request(self.user, 'post', 'scraps', scrap_data2)
        # 잘못된 field로 post request 요청
        assert response2.status_code == 400

    def test_scrap_same_article(self):
        scrap_data = {
            'parent_article': self.article.id
        }
        # 중복 스크랩
        self.http_request(self.user, 'post', 'scraps', scrap_data)
        # 같은 scrap을 한번 더 생성
        # 어색해보이는 방법이지만, 링크 참고: https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        try:
            with transaction.atomic():
                self.http_request(self.user, 'post', 'scraps', scrap_data)
        except IntegrityError:
            pass

        # 중복 스크랩 허용하지 않음
        assert Scrap.objects.filter(parent_article=self.article, scrapped_by=self.user).count() == 1

    def test_scrap_sexual(self):
        # 성인글에 대한 profile 설정 했을 때
        Scrap.objects.create(parent_article=self.article_sexual, scrapped_by=self.user)

        self.user.profile.see_sexual = True
        scrap = self.http_request(self.user, 'get', 'scraps').data

        # 성인글 보도록 하면 scrap한 글이 보임
        assert scrap.get('num_items') == 1
        assert not scrap.get('results')[0].get('parent_article').get('is_hidden')

        self.user.profile.see_sexual = False
        scrap2 = self.http_request(self.user, 'get', 'scraps').data

        # 성인글 안보도록 바꾸면 scrap한 글이 안보임
        assert scrap2.get('results')[0].get('parent_article').get('is_hidden')

    def test_scrap_social(self):
        # 정치글에 대한 profile 설정 했을 때
        Scrap.objects.create(parent_article=self.article_social, scrapped_by=self.user)

        self.user.profile.see_social = True
        scrap = self.http_request(self.user, 'get', 'scraps').data

        # 정치글 보도록 하면 scrap한 글이 보임
        assert scrap.get('num_items') == 1
        assert not scrap.get('results')[0].get('parent_article').get('is_hidden')

        self.user.profile.see_social = False
        scrap2 = self.http_request(self.user, 'get', 'scraps').data

        # 정치글 안보도록 바꾸면 scrap한 글이 안보임
        assert scrap2.get('results')[0].get('parent_article').get('is_hidden')

    @pytest.mark.usefixtures('set_block')
    def test_scrap_block(self):
        # user2가 user을 차단했을 때 user2가 user의 article을 scrap 하는 경우 안 보이는지 확인
        Scrap.objects.create(parent_article=self.article, scrapped_by=self.user2)

        scrap = self.http_request(self.user2, 'get', 'scraps').data
        assert scrap.get('num_items') == 1
        assert scrap.get('results')[0].get('parent_article').get('is_hidden')
