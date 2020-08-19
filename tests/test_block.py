import pytest
from django.test import TestCase
from django.utils import timezone
from django.db.utils import IntegrityError
from apps.core.models import Article, Topic, Board, Comment, Block
from tests.conftest import RequestSetting


@pytest.fixture(scope='class')
def set_board(request):
    request.cls.board = Board.objects.create(
        slug='test board',
        ko_name='테스트 게시판',
        en_name='Test Board',
        ko_description='테스트 게시판입니다',
        en_description='This is a board for testing'
    )


@pytest.fixture(scope='class')
def set_topic(request):
    """set_board 먼저 적용"""
    request.cls.topic = Topic.objects.create(
        slug='test topic',
        ko_name='테스트 토픽',
        en_name='Test Topic',
        ko_description='테스트용 토픽입니다',
        en_description='This is topic for testing',
        parent_board=request.cls.board
    )


@pytest.fixture(scope='class')
def set_articles(request):
    """set_topic, set_user_client 먼저 적용"""
    request.cls.article = Article.objects.create(
        title='Test Article',
        content='Content of test article',
        content_text='Content of test article in text',
        is_anonymous=False,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now()
    )

    request.cls.article2 = Article.objects.create(
        title='Test Article 2',
        content='Content of test article 2',
        content_text='Content of test article in text 2',
        is_anonymous=False,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user2,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now()
    )

    request.cls.article3 = Article.objects.create(
        title='Test Article 3',
        content='Content of test article 3',
        content_text='Content of test article in text 3',
        is_anonymous=False,
        is_content_sexual=False,
        is_content_social=False,
        hit_count=0,
        positive_vote_count=0,
        negative_vote_count=0,
        created_by=request.cls.user3,
        parent_topic=request.cls.topic,
        parent_board=request.cls.board,
        commented_at=timezone.now()
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_user_client3', 'set_board', 'set_topic',
                         'set_articles')
class TestBlock(TestCase, RequestSetting):
    # block 개수를 확인
    def test_block_list(self):
        res = self.http_request(self.user, 'get', 'blocks')
        assert res.data.get('num_items') == 0

        Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )
        Block.objects.create(
            blocked_by=self.user,
            user=self.user3
        )

        res = self.http_request(self.user, 'get', 'blocks')
        assert res.data.get('num_items') == 2
        assert Block.objects.filter(blocked_by=self.user.id).count() == 2

    # POST로 block이 생성되는지 확인
    def test_create_block(self):
        # user2가 user를 차단
        block_data = {
            'blocked_by': self.user2.id,
            'user': self.user.id
        }
        self.http_request(self.user2, 'post', 'blocks', block_data)
        assert Block.objects.filter(blocked_by=self.user2.id, user=self.user.id)

    # GET으로 block 가져오기
    def test_get_block(self):
        block = Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )

        res = self.http_request(self.user, 'get', f'blocks/{block.id}').data
        assert res.get('blocked_by') == self.user.id
        assert res.get('user').get('id') == self.user2.id

    # 이미 차단된 유저를 중복 차단하는 경우 확인
    def test_cannot_block_already_blocked_user(self):
        block_data = {
            'blocked_by': self.user2.id,
            'user': self.user.id
        }

        # 같은 block을 2번 생성
        self.http_request(self.user2, 'post', 'blocks', block_data)
        self.http_request(self.user2, 'post', 'blocks', block_data)

        # 중복 차단이 허용되지 않으면 아래 테스트가 패스해야 합니다
        assert Block.objects.filter(blocked_by=self.user2.id, user=self.user.id).count() == 1

    # 쌍방향 차단이 되는 것 확인 (user 둘이 서로 차단)
    def test_mutual_block(self):
        # user가 user2를 차단
        block1 = Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )

        # user2가 user를 차단
        block2 = Block.objects.create(
            blocked_by=self.user2,
            user=self.user,
        )

        assert Block.objects.filter(blocked_by=self.user.id, user=self.user2.id)
        assert Block.objects.filter(blocked_by=self.user2.id, user=self.user.id)

    # 차단한 유저들의 글이 보이지 않음을 확인
    def test_get_articles_by_blocked_user(self):
        # 차단 전에는 모든 글이 보이는 것 확인
        res = self.http_request(self.user, 'get', 'articles').data
        for post in res.get('results'):
            assert not post.get('is_hidden')

        # user가 user2를 차단
        block = Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )

        # user가 글 목록을 가져올때, 차단된 user2의 글이 hidden인지 확인
        hidden_cnt = 0
        res = self.http_request(self.user, 'get', 'articles').data
        for post in res.get('results'):
            hidden = post.get('is_hidden')
            writer_id = post.get('created_by').get('id')
            if writer_id == self.user2.id:
                assert hidden
                hidden_cnt = hidden_cnt + 1
            else:
                assert not hidden
        assert hidden_cnt == 1

        # user가 user3를 차단
        block2 = Block.objects.create(
            blocked_by=self.user,
            user=self.user3,
        )

        # user가 글 목록을 가져올때, 차단된 user2, user3의 글이 모두 hidden인지 확인
        hidden_cnt = 0
        res = self.http_request(self.user, 'get', 'articles').data
        for post in res.get('results'):
            hidden = post.get('is_hidden')
            writer_id = post.get('created_by').get('id')
            if writer_id == self.user2.id or writer_id == self.user3.id:
                assert hidden
                hidden_cnt = hidden_cnt + 1
            else:
                assert not hidden
        assert hidden_cnt == 2

    # 차단한 유저가 익명 글을 써도 나에게 보이지 않는 것 확인
    def test_get_anonymous_articles_by_blocked_user(self):
        # user2가 익명 글을 작성
        anon_article = Article.objects.create(
                            title='Test Article',
                            content='Content of test article',
                            content_text='Content of test article in text',
                            is_anonymous=False,
                            is_content_sexual=False,
                            is_content_social=False,
                            hit_count=0,
                            positive_vote_count=0,
                            negative_vote_count=0,
                            created_by=self.user2,
                            parent_topic=self.topic,
                            parent_board=self.board,
                            commented_at=timezone.now()
                        )

        # user가 user2를 차단
        block = Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )

        # user가 글을 가져오면, 차단된 user2의 익명글도 hidden 처리 되는지 확인
        res = self.http_request(self.user, 'get', 'articles').data
        found = False
        for post in res.get('results'):
            if post.get('id') == anon_article.id:
                assert post.get('is_hidden')
                found = True
                break

        assert found

    # 차단한 유저의 댓글이 보이지 않음을 확인
    def test_comment_by_blocked_user(self):
        # user2가 댓글을 씀
        blocked_comment = Comment.objects.create(
                                content='this is a test comment',
                                is_anonymous=False,
                                created_by=self.user2,
                                parent_article=self.article,
                            )

        not_blocked_comment = Comment.objects.create(
                                    content='this is a test comment',
                                    is_anonymous=False,
                                    created_by=self.user3,
                                    parent_article=self.article,
                                )

        # user가 user2를 차단
        block = Block.objects.create(
            blocked_by=self.user,
            user=self.user2,
        )

        # user에게 차단된 user2의 댓글이 hidden인지 확인
        res = self.http_request(self.user, 'get', f'comments/{blocked_comment.id}').data
        assert res.get('is_hidden')

        # user에게 차단되지 않은 user3의 댓글은 hidden이 아닌 것 확인
        res = self.http_request(self.user, 'get', f'comments/{not_blocked_comment.id}').data
        assert not res.get('is_hidden')

    # DELETE로 차단 해제할 수 있음 (차단 해제 후 그 사람의 모든 글이 잘 보임)
    def test_unblock(self):
        # user가 user2를 차단
        block = Block.objects.create(
                    blocked_by=self.user,
                    user=self.user2,
                )
        res = self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        assert res.get('is_hidden')

        # 차단 취소
        self.http_request(self.user, 'delete', f'blocks/{block.id}')
        assert not Block.objects.filter(id=block.id)

        # user2의 글(article2)이 보이는지 확인
        res = self.http_request(self.user, 'get', f'articles/{self.article2.id}').data
        assert not res.get('is_hidden')

    # 유저가 자기 자신을 차단할수 없는 것 확인 (생성 과정에서 Integrity Error가 발생해야 함)
    def test_block_self(self):
        try:
            Block.objects.create(
                blocked_by=self.user,
                user=self.user,
                )
        except IntegrityError:
            assert True
        else:
            assert False
