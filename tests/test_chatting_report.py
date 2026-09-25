import pytest
from django.core import mail

from apps.chatting.models import ChatMessage
from apps.core.models import Report
from apps.delivery.models import DeliveryParty
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures("set_user_client", "set_user_client2", "set_user_client3")
class TestChatReport(TestCase, RequestSetting):
    # 익명 배달방: 방장 user / 익명1 user2 / user3 은 방 밖
    def setUp(self):
        self.party = DeliveryParty.open(
            self.user, store_name="가게", place_name="희망관", min_order_amount=100000,
            recruit_minutes=30, price=1000,
        )
        self.party.join(self.user2)
        self.room = self.party.chat_room

    def report(self, user, body):
        return self.http_request(user, "post", "reports", {"type": "insult", "content": "욕했어요", **body})

    def test_report_member_by_anon_number(self):
        res = self.report(self.user2, {"chat_room": self.room.id, "anon_number": 0})
        assert res.status_code == 201
        # 응답에는 신고 id 만 있다
        assert set(res.data) == {"id"}

        report = Report.objects.get(pk=res.data["id"])
        assert report.target_type == "chat_member"
        assert report.reported_user == self.user
        assert report.anon_number == 0
        assert report.reporter_email == self.user2.email
        assert report.reported_email == self.user.email
        # 관리자에게 메일이 간다
        assert len(mail.outbox) == 1

    def test_report_message(self):
        message = ChatMessage.create(chat_room=self.room, created_by=self.user, message_type="TEXT", message_content="x")
        res = self.report(self.user2, {"chat_message": message.id})
        assert res.status_code == 201
        report = Report.objects.get(pk=res.data["id"])
        assert report.target_type == "chat_message"
        assert report.chat_message == message

    def test_my_report_list_hides_emails(self):
        self.report(self.user2, {"chat_room": self.room.id, "anon_number": 0})
        res = self.http_request(self.user2, "get", "reports")
        assert res.status_code == 200
        item = res.data["results"][0]
        for key in ("reported_user", "reporter_email", "reported_email"):
            assert key not in item

    def test_rules(self):
        # 방 밖 사람은 신고할 수 없다
        assert self.report(self.user3, {"chat_room": self.room.id, "anon_number": 0}).status_code == 403
        # 자기 자신
        assert self.report(self.user2, {"chat_room": self.room.id, "anon_number": 1}).status_code == 400
        # 없는 번호
        assert self.report(self.user2, {"chat_room": self.room.id, "anon_number": 9}).status_code == 400
        # 안내 메시지는 신고할 수 없다
        system = self.room.message_set.filter(message_type="SYSTEM").first()
        assert self.report(self.user2, {"chat_message": system.id}).status_code == 400
        # 24시간 안에 같은 사람을 다시 신고
        assert self.report(self.user2, {"chat_room": self.room.id, "anon_number": 0}).status_code == 201
        res = self.report(self.user2, {"chat_room": self.room.id, "anon_number": 0})
        assert res.status_code == 400
        assert res.data["detail"] == "이미 신고했어요."
