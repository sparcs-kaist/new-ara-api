import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.chatting.models import (
    ChatMessage,
    ChatPaymentRequest,
    ChatRoom,
    ChatRoomMemberShip,
    ChatRoomType,
    ChatUserRole,
    ChatVote,
)
from apps.chatting.models.room import ChatNameType
from apps.delivery.models import DeliveryParty
from tests.conftest import RequestSetting, TestCase, Utils


# 항목 수가 늘어도 쿼리 수가 같아야 한다 (N+1 방지)
@pytest.mark.usefixtures("set_user_client")
class TestQueryCount(TestCase, RequestSetting):
    def count_queries(self, method, path, querystring=""):
        with CaptureQueriesContext(connection) as ctx:
            res = self.http_request(self.user, method, path, querystring=querystring)
        assert res.status_code == 200, res.data
        return len(ctx.captured_queries)

    def make_room(self, members):
        room = ChatRoom.objects.create(
            room_title="방", room_type=ChatRoomType.GROUP_DM.value, chat_name_type=ChatNameType.ANONYMOUS.value,
        )
        ChatRoomMemberShip.objects.create(chat_room=room, user=self.user, role=ChatUserRole.OWNER.value)
        for user in members:
            ChatRoomMemberShip.objects.create(chat_room=room, user=user)
        return room

    def add_messages(self, room, users, count):
        for i in range(count):
            user = users[i % len(users)]
            ChatMessage.create(chat_room=room, created_by=user, message_type="TEXT", message_content=f"m{i}")
            ChatVote.create_with_message(room, user, f"v{i}", ["a", "b"], 1).cast(self.user, [])
            ChatPaymentRequest.create_with_message(room, user, "은행", "1", [(self.user, 1000)])

    def test_message_list(self):
        users = Utils.create_users(4)
        room = self.make_room(users)
        self.add_messages(room, users, 1)
        small = self.count_queries("get", "chat/message", f"chat_room={room.id}")
        self.add_messages(room, users, 5)
        large = self.count_queries("get", "chat/message", f"chat_room={room.id}")
        assert small == large

    def make_dm(self, other):
        room = ChatRoom.objects.create(room_title="DM", room_type=ChatRoomType.DM.value)
        ChatRoomMemberShip.objects.create(chat_room=room, user=self.user)
        ChatRoomMemberShip.objects.create(chat_room=room, user=other)
        return room

    def test_room_list(self):
        users = Utils.create_users(8)
        for _ in range(2):
            self.add_messages(self.make_room(users[:3]), users[:3], 1)
        self.make_dm(users[3])
        small = self.count_queries("get", "chat/room")
        for _ in range(5):
            self.add_messages(self.make_room(users[:3]), users[:3], 1)
        for user in users[4:]:
            self.make_dm(user)
        large = self.count_queries("get", "chat/room")
        assert small == large

    def test_room_detail(self):
        room = self.make_room(Utils.create_users(2))
        small = self.count_queries("get", f"chat/room/{room.id}")
        for user in Utils.create_users(8)[2:]:
            ChatRoomMemberShip.objects.create(chat_room=room, user=user)
        large = self.count_queries("get", f"chat/room/{room.id}")
        assert small == large

    def test_delivery_list_and_detail(self):
        def open_party():
            return DeliveryParty.open(
                self.user, store_name="가게", place_name="희망관", min_order_amount=100000,
                recruit_minutes=30, price=1000,
            )

        party = open_party()
        users = Utils.create_users(8)
        small_list = self.count_queries("get", "delivery")
        small_detail = self.count_queries("get", f"delivery/{party.id}")
        for _ in range(4):
            open_party()
        for user in users:
            party.join(user)
            party.place_order(user, price=1000)
        assert self.count_queries("get", "delivery") == small_list
        assert self.count_queries("get", f"delivery/{party.id}") == small_detail

    def test_message_notification(self):
        # 메시지 알림은 메시지마다 동기로 돈다. 방 인원이 늘어도 쿼리 수가 같아야 한다
        def send_count(room):
            with CaptureQueriesContext(connection) as ctx:
                ChatMessage.create(chat_room=room, created_by=self.user, message_type="TEXT", message_content="x")
            return len(ctx.captured_queries)

        users = Utils.create_users(10)
        small = send_count(self.make_room(users[:2]))
        large = send_count(self.make_room(users))
        assert small == large
