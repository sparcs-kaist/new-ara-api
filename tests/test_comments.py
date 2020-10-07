import pytest
from django.utils import timezone
from apps.core.models import Article, Topic, Board, Comment
from tests.conftest import RequestSetting, TestCase


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
def set_article(request):
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


@pytest.fixture(scope='class')
def set_comment(request):
    """set_article 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content='this is a test comment',
        is_anonymous=False,
        created_by=request.cls.user,
        parent_article=request.cls.article,
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_article', 'set_comment')
class TestComments(TestCase, RequestSetting):
    # comment 개수를 확인하는 테스트
    def test_comment_list(self):
        # number of comments is initially 0
        res = self.http_request(self.user, 'get', f'articles/{self.article.id}')
        assert res.data.get('comment_count') == 1

        comment2 = Comment.objects.create(
                        content='Test comment 2',
                        is_anonymous=False,
                        created_by=self.user,
                        parent_article=self.article
                    )
        comment3 = Comment.objects.create(
                        content='Test comment 3',
                        is_anonymous=False,
                        created_by=self.user,
                        parent_article=self.article
                    )

        res = self.http_request(self.user, 'get', f'articles/{self.article.id}')
        assert res.data.get('comment_count') == 3

    # post로 댓글 생성됨을 확인
    def test_create_comment(self):
        comment_str = 'this is a test comment for test_create_comment'
        comment_data = {
            'content': comment_str,
            'parent_article': self.article.id,
        }
        self.http_request(self.user, 'post', 'comments', comment_data)
        assert Comment.objects.filter(content=comment_str)

    # post로 대댓글이 생성됨을 확인
    def test_create_subcomment(self):
        subcomment_str = 'this is a test subcomment'
        subcomment_data = {
            'content': subcomment_str,
            'parent_comment': self.comment.id,
        }
        self.http_request(self.user, 'post', 'comments', subcomment_data)
        assert Comment.objects.filter(content=subcomment_str, parent_comment=self.comment.id)

    # 댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count(self):
        article = Article.objects.get(id=self.article.id)
        assert article.comment_count == 1
        Comment.objects.filter(id=self.comment.id).delete()
        assert article.comment_count == 0

    # 대댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count_with_subcomments(self):
        subcomment1 = Comment.objects.create(
            content='Test comment 3',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )
        subcomment2 = Comment.objects.create(
            content='Test comment 3',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )
        article = Article.objects.get(id=self.article.id)
        assert article.comment_count == 3

        # 대댓글, 댓글을 지우면 comment_count 1씩 감소
        Comment.objects.filter(id=subcomment2.id).delete()
        assert article.comment_count == 2

        Comment.objects.filter(id=self.comment.id).delete()
        assert article.comment_count == 1

    # get으로 comment가 잘 retrieve 되는지 확인
    def test_retrieve_comment(self):
        res = self.http_request(self.user, 'get', f'comments/{self.comment.id}').data
        assert res.get('content') == self.comment.content
        assert res.get('parent_article') == self.comment.parent_article.id

    # 댓글 작성자가 자신의 댓글을 지울 수 있는지 확인
    def test_delete_comment_by_comment_writer(self):
        assert Comment.objects.filter(id=self.comment.id)
        self.http_request(self.user, 'delete', f'comments/{self.comment.id}')
        assert not Comment.objects.filter(id=self.comment.id)

    # 다른 사용자의 댓글을 지울 수 없는 것 확인
    def test_delete_comment_by_not_comment_writer(self):
        assert Comment.objects.filter(id=self.comment.id)
        self.http_request(self.user2, 'delete', f'comments/{self.comment.id}')
        assert Comment.objects.filter(id=self.comment.id)

    # 댓글을 삭제할 때, 그 댓글의 대댓글은 삭제되지 않는 것 확인
    def test_delete_comment_with_subcomment(self):
        subcomment = Comment.objects.create(
            content='Test subcomment',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )
        Comment.objects.filter(id=self.comment.id).delete()
        assert Comment.objects.filter(id=subcomment.id)

    # patch로 댓글을 수정할 수 있음을 확인
    def test_edit_comment_by_writer(self):
        edited_content = 'this is an edited test comment'
        edited_comment_data = {
            'content': edited_content,
        }
        self.http_request(self.user, 'patch', f'comments/{self.comment.id}', edited_comment_data)
        assert Comment.objects.get(id=self.comment.id).content == edited_content

    # 다른 사용자의 댓글을 수정할 수 없는 것 확인
    def test_edit_comment_by_nonwriter(self):
        original_content = self.comment.content
        edited_comment_data = {
            'content': 'this is an edited test comment',
        }
        self.http_request(self.user2, 'patch', f'comments/{self.comment.id}', edited_comment_data)
        assert Comment.objects.get(id=self.comment.id).content == original_content

    # http get으로 익명 댓글을 retrieve했을 때 작성자가 익명으로 나타나는지 확인
    def test_comment_anonymity(self):
        anonymous_comment = Comment.objects.create(
                                content='Anonymous test comment',
                                is_anonymous=True,
                                created_by=self.user,
                                parent_article=self.article
                            )

        assert self.http_request(self.user, 'get', f'comments/{anonymous_comment.id}').data.get('created_by') == '익명'
        assert self.http_request(self.user2, 'get', f'comments/{anonymous_comment.id}').data.get('created_by') == '익명'

    # 댓글 좋아요 확인
    def test_positive_vote(self):
        # 좋아요 2표
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_positive')
        self.http_request(self.user2, 'post', f'comments/{self.comment.id}/vote_positive')

        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 2
        assert comment.negative_vote_count == 0

    # 댓글 싫어요 확인
    def test_negative_vote(self):
        # 싫어요 2표
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_negative')
        self.http_request(self.user2, 'post', f'comments/{self.comment.id}/vote_negative')

        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 2

    # 투표 취소 후 재투표 가능한 것 확인
    def test_vote_undo_and_redo(self):
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_positive')

        # 투표 취소
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_cancel')
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 0

        # 재투표
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_positive')
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 1
        assert comment.negative_vote_count == 0

    # 댓글 중복 투표 안되는 것 확인. 중복투표시, 맨 마지막 투표 결과만 유효함
    def test_cannot_vote_both(self):
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_positive')
        self.http_request(self.user, 'post', f'comments/{self.comment.id}/vote_negative')
        comment = Comment.objects.get(id=self.comment.id)
        assert comment.positive_vote_count == 0
        assert comment.negative_vote_count == 1
