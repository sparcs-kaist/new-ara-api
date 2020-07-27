import pytest
from django.test import TestCase
from tests.conftest import RequestSetting

from apps.core.models import Notification, NotificationReadLog, Article, Board, Comment


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


@pytest.fixture(scope='class')
def set_comment(request):
    """set_articles 먼저 적용"""
    request.cls.comment = Comment.objects.create(
        content='댓글입니다.',
        created_by=request.cls.user2,
        parent_article=request.cls.article
    )


@pytest.mark.usefixtures('set_user_clients', 'set_board', 'set_articles', 'set_comment')
class TestNotification(TestCase, RequestSetting):
    def test_notification_article_commented(self):
        self.api_client.force_authenticate(user=self.user)
        notifications = self.http_request('get', 'notifications')

        # user에게 알림: user의 글에 user2가 댓글을 달아서
        assert notifications.status_code == 200
        assert Notification.objects.all().count() == 1

        assert notifications.data.get('num_items') == 1

    def test_notification_comment_commented(self):
        Comment.objects.create(
            content='대댓글입니다.',
            created_by=self.user,
            parent_comment=self.comment
        )

        self.api_client.force_authenticate(user=self.user2)
        notifications = self.http_request('get', 'notifications')

        # user2에게 알림: user2의 댓글에 user가 대댓글을 달아서
        assert notifications.status_code == 200
        assert Notification.objects.all().count() == 2

        assert notifications.data.get('num_items') == 1

'''
@pytest.mark.usefixtures('set_user_clients', 'set_board', 'set_articles', 'set_comments')
class TestNotificationReadLog(TestCase, RequestSetting):
    def test_read(self):
        notification = Notification.objects.first()

        print(notification.__dict__)
        noti_dict = {'user': self.user.id}

        notification_read = self.http_request('post', f'notifications/{notification.id}/read', noti_dict)

        assert notification_read.status_code == 200

        # gets error
        # check is_read == true
        notification_read_log = NotificationReadLog.objects.filter(read_by=self.user, notification=notification).all()

        print (notification_read_log.__dict__)

        assert notification_read_log.is_read


    def test_read_all(self):
        Notification.objects.create(
            type='article_commented',
            title='테스트1',
            content='내용1',
            related_article=self.article
        )

        Notification.objects.create(
            type='comment_commented',
            title='테스트2',
            content='내용2',
            related_comment=self.comment
        )

        noti_dict = {'user': self.user.id}

        notification_read = self.http_request('post', 'notifications/read_all', noti_dict)
        assert notification_read.status_code == 200

        # gets error
        # check is_read == true
        for noti in notification_read:
            print(noti)
            notification_read_log = NotificationReadLog.objects.filter(read_by=self.user, notification=noti).first()
            assert notification_read_log.is_read
'''