import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from apps.core.models import Article, Topic, Board, Comment, Block
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

    """set_topic, set_user_client 먼저 적용"""
    request.cls.article_anonymous = Article.objects.create(
        title='Anonymous Test Article',
        content='Content of test article',
        content_text='Content of test article in text',
        is_anonymous=True,
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
def set_comments(request):
    """set_article 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content='this is a test comment',
        is_anonymous=False,
        created_by=request.cls.user,
        parent_article=request.cls.article,
    )

    request.cls.comment_anonymous = Comment.objects.create(
        content='this is an anonymous test comment',
        is_anonymous=True,
        created_by=request.cls.user,
        parent_article=request.cls.article_anonymous,
    )


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_articles', 'set_comments')
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
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(content=comment_str)

    # post로 대댓글이 생성됨을 확인
    def test_create_subcomment(self):
        subcomment_str = 'this is a test subcomment'
        subcomment_data = {
            'content': subcomment_str,
            'parent_comment': self.comment.id,
        }
        self.http_request(self.user, 'post', 'comments', subcomment_data)
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(content=subcomment_str, parent_comment=self.comment.id)

    # 댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count(self):
        article = Article.objects.get(id=self.article.id)
        assert article.comment_count == 1
        comment = Comment.objects.get(id=self.comment.id)
        comment.delete()
        article.refresh_from_db(fields=['comment_count'])
        assert article.comment_count == 0

    # 대댓글의 생성과 삭제에 따라서 article의 comment_count가 맞게 바뀌는지 확인
    def test_article_comment_count_with_subcomments(self):

        article = Article.objects.get(id=self.article.id)
        print('comment set: ', article.comment_set)
        assert article.comment_count == 1

        subcomment1 = Comment.objects.create(
            content='Test comment 2',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )

        article = Article.objects.get(id=self.article.id)
        print('comment set: ', article.comment_set)
        assert article.comment_count == 2

        subcomment2 = Comment.objects.create(
            content='Test comment 3',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )

        article = Article.objects.get(id=self.article.id)
        print('comment set: ', article.comment_set)
        assert article.comment_count == 3

        # 대댓글 삭제
        comment = Comment.objects.get(id=subcomment2.id)
        comment.delete()
        article.refresh_from_db(fields=['comment_count'])
        assert article.comment_count == 2

    # get으로 comment가 잘 retrieve 되는지 확인
    def test_retrieve_comment(self):
        res = self.http_request(self.user, 'get', f'comments/{self.comment.id}').data
        assert res.get('content') == self.comment.content
        assert res.get('parent_article') == self.comment.parent_article.id

    # 댓글 작성자가 자신의 댓글을 지울 수 있는지 확인
    def test_delete_comment_by_comment_writer(self):
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(id=self.comment.id)
        self.http_request(self.user, 'delete', f'comments/{self.comment.id}')
        assert not Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(id=self.comment.id)

    # 다른 사용자의 댓글을 지울 수 없는 것 확인
    def test_delete_comment_by_not_comment_writer(self):
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(id=self.comment.id)
        self.http_request(self.user2, 'delete', f'comments/{self.comment.id}')
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(id=self.comment.id)

    # 댓글을 삭제할 때, 그 댓글의 대댓글은 삭제되지 않는 것 확인
    def test_delete_comment_with_subcomment(self):
        subcomment = Comment.objects.create(
            content='Test subcomment',
            is_anonymous=False,
            created_by=self.user,
            parent_comment=self.comment
        )
        comment = Comment.objects.filter(id=self.comment.id).get()
        # MetaDataModel class에서 delete하여 signal로 cascade 삭제 확인.
        comment.delete()
        assert Comment.objects.filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc)).filter(id=subcomment.id)

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
    def test_anonymous_comment(self):
        # 익명 댓글 생성
        anon_comment = Comment.objects.create(
                                content='Anonymous test comment',
                                is_anonymous=True,
                                created_by=self.user,
                                parent_article=self.article
                            )

        # 익명 댓글을 GET할 때, 작성자의 정보가 전달되지 않는 것 확인
        res = self.http_request(self.user, 'get', f'comments/{anon_comment.id}').data
        assert res.get('is_anonymous')
        assert res.get('created_by')['username'] != anon_comment.created_by.username

        res2 = self.http_request(self.user2, 'get', f'comments/{anon_comment.id}').data
        assert res2.get('is_anonymous')
        assert res2.get('created_by')['username'] != anon_comment.created_by.username

    # 익명글의 글쓴이가 본인의 글에 남긴 댓글에 대해, user_id가 같은지 확인
    def test_anonymous_comment_by_article_writer(self):
        # 익명 댓글 생성
        Comment.objects.create(
            content='Anonymous test comment',
            is_anonymous=True,
            created_by=self.user,
            parent_article=self.article
        )

        r_article = self.http_request(self.user, 'get', f'articles/{self.article_anonymous.id}').data
        article_auther_id = r_article.get('created_by')['id']
        r_comment = self.http_request(self.user, 'get', f'comments/{self.comment_anonymous.id}').data
        comment_auther_id = r_comment.get('created_by')['id']
        assert article_auther_id == comment_auther_id

        r_article2 = self.http_request(self.user2, 'get', f'articles/{self.article_anonymous.id}').data
        article_auther_id2 = r_article2.get('created_by')['id']
        r_comment2 = self.http_request(self.user2, 'get', f'comments/{self.comment_anonymous.id}').data
        comment_auther_id2 = r_comment2.get('created_by')['id']
        assert article_auther_id2 == comment_auther_id2

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


@pytest.mark.usefixtures('set_user_client', 'set_user_client2', 'set_board', 'set_topic', 'set_articles', 'set_comments') 
class TestHiddenComments(TestCase, RequestSetting):
    def _comment_factory(self, **comment_kwargs):
        return Comment.objects.create(
            content='example comment',
            is_anonymous=False,
            created_by=self.user,
            parent_article=self.article,
            **comment_kwargs
        )

    def _test_can_override(self, user: User, target_comment: Comment, expected: bool):
        res = self.http_request(user, 'get', f'comments/{target_comment.id}', None, 'override_hidden').data
        assert res.get('hidden_content') is None
        assert res.get('why_hidden') is not None
        assert res.get('why_hidden') != []
        assert res.get('is_hidden') != expected
        if expected:
            assert res.get('content') is not None
        else:
            assert res.get('content') is None

    def test_blocked_user_block(self):
        Block.objects.create(
            blocked_by=self.user,
            user=self.user2
        )

        comment2 = Comment.objects.create(
            content='example comment',
            is_anonymous=False,
            created_by=self.user2,
            parent_article=self.article
        )

        res = self.http_request(self.user, 'get', f'comments/{comment2.id}').data
        assert res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert 'BLOCKED_USER_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.user, comment2, True)

    def test_reported_comment_block(self):
        target_comment = self._comment_factory(
            report_count=1000000,
            hidden_at=timezone.now()
        )

        res = self.http_request(self.user, 'get', f'comments/{target_comment.id}').data
        assert not res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('content') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert 'REPORTED_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.user, target_comment, False)

    def test_deleted_comment_block(self):
        target_comment = self._comment_factory(
            deleted_at=timezone.now()
        )

        res = self.http_request(self.user, 'get', f'comments/{target_comment.id}').data
        assert not res.get('can_override_hidden')
        assert res.get('is_hidden')
        assert res.get('title') is None
        assert res.get('content') is None
        assert res.get('hidden_title') is None
        assert res.get('hidden_content') is None
        assert 'DELETED_CONTENT' in res.get('why_hidden')
        self._test_can_override(self.user, target_comment, False)
