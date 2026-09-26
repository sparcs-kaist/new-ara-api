from unittest.mock import patch

import pytest

from apps.chatting.models import ChatMessage, ChatRoom, ChatRoomMemberShip, ChatRoomType, ChatUserRole
from apps.core.models import NotificationReadLog
from apps.user.models import UserNotificationPreference
from tests.conftest import TestCase

PUSH = "apps.core.models.notification.enqueue_push_for_notification_to_users"


@pytest.mark.usefixtures("set_user_client", "set_user_client2", "set_user_client3")
class TestNotificationPreference(TestCase):
    # 기존 api/me 처럼 끝에 / 가 없는 주소라 http_request 대신 직접 부른다
    def call(self, method, data=None):
        self.api_client.force_authenticate(user=self.user)
        return getattr(self.api_client, method)("/api/me/notification_preference", data=data, format="json")

    def test_default_is_all_on(self):
        res = self.call("get")
        assert res.status_code == 200
        assert res.data == {
            "article_commented": True, "comment_commented": True, "chat_message": True, "delivery": True,
        }

    def test_turn_off_chat(self):
        res = self.call("patch", {"chat_message": False})
        assert res.status_code == 200
        assert res.data["chat_message"] is False
        assert UserNotificationPreference.objects.get(user=self.user).chat_message is False

    def test_delivery_off_needs_confirm(self):
        res = self.call("patch", {"delivery": False})
        assert res.status_code == 400
        assert res.data["code"] == "confirm_required"
        assert "책임" in res.data["detail"]

        res = self.call("patch", {"delivery": False, "confirm_delivery_off": True})
        assert res.status_code == 200
        assert res.data["delivery"] is False

    def test_chat_push_skips_muted_but_keeps_notification(self):
        room = ChatRoom.objects.create(room_title="방", room_type=ChatRoomType.GROUP_DM.value)
        for user in (self.user, self.user2, self.user3):
            ChatRoomMemberShip.objects.create(chat_room=room, user=user, role=ChatUserRole.PARTICIPANT.value)
        ChatRoomMemberShip.objects.filter(chat_room=room).update(last_seen_at=None)
        UserNotificationPreference.objects.create(user=self.user3, chat_message=False)

        with patch(PUSH) as push:
            ChatMessage.create(chat_room=room, created_by=self.user, message_type="TEXT", message_content="안녕")

        assert push.call_args.args[1] == [self.user2.id]
        assert push.call_args.kwargs["collapse_key"] == f"room-{room.id}"
        assert NotificationReadLog.objects.filter(read_by=self.user3).exists()


@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestChatPushDedup(TestCase):
    def test_skip_while_unread_and_resume_after_reading(self):
        from django.utils import timezone

        room = ChatRoom.objects.create(room_title="방", room_type=ChatRoomType.GROUP_DM.value)
        for user in (self.user, self.user2):
            ChatRoomMemberShip.objects.create(chat_room=room, user=user, role=ChatUserRole.PARTICIPANT.value)

        def send():
            with patch(PUSH) as push:
                ChatMessage.create(chat_room=room, created_by=self.user, message_type="TEXT", message_content="x")
            return push.call_args.args[1] if push.called else []

        assert send() == [self.user2.id]
        assert send() == []
        ChatRoomMemberShip.objects.filter(chat_room=room, user=self.user2).update(last_seen_at=timezone.now())
        assert send() == [self.user2.id]


@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestDeliveryPushQueue(TestCase):
    def test_delivery_event_uses_urgent_queue_and_own_collapse_key(self):
        from apps.delivery.models import DeliveryParty

        party = DeliveryParty.open(
            self.user, store_name="가게", place_name="희망관", min_order_amount=1000,
            recruit_minutes=30, price=1000,
        )
        party.join(self.user2)
        party.confirm_order(self.user)
        with patch(PUSH) as push:
            party.arrive(self.user)
        assert push.call_args.kwargs["queue"] == "urgent"
        assert push.call_args.kwargs["collapse_key"] == f"delivery-{party.chat_room_id}"


@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestChatPushText(TestCase):
    def send(self, room, **kwargs):
        from apps.core.models import Notification

        ChatMessage.create(chat_room=room, created_by=self.user, **kwargs)
        return Notification.objects.filter(related_chat_room=room).latest("id")

    def test_group_room_title_and_sender_preview(self):
        room = ChatRoom.objects.create(room_title="스터디", room_type=ChatRoomType.GROUP_DM.value)
        for user in (self.user, self.user2):
            ChatRoomMemberShip.objects.create(chat_room=room, user=user, role=ChatUserRole.PARTICIPANT.value)
        notification = self.send(room, message_type="TEXT", message_content="내일 몇 시?")
        assert notification.title == "스터디"
        assert notification.content == f"{self.user.profile.nickname}: 내일 몇 시?"

    def test_dm_title_is_sender_and_photo_preview(self):
        room = ChatRoom.objects.create(room_title="DM_a,b", room_type=ChatRoomType.DM.value)
        for user in (self.user, self.user2):
            ChatRoomMemberShip.objects.create(chat_room=room, user=user, role=ChatUserRole.PARTICIPANT.value)
        notification = self.send(room, message_type="IMAGE", message_content="https://x.com/a.png")
        assert notification.title == self.user.profile.nickname
        assert notification.content == "사진"

    def test_anonymous_delivery_room_uses_anon_name(self):
        from apps.delivery.models import DeliveryParty

        party = DeliveryParty.open(
            self.user2, store_name="가게", place_name="희망관", min_order_amount=100000,
            recruit_minutes=30, price=1000,
        )
        party.join(self.user)
        notification = self.send(party.chat_room, message_type="TEXT", message_content="안녕하세요")
        assert notification.title == "가게"
        assert notification.content == "익명1: 안녕하세요"
        party.place_order(self.user, price=3000)
        from apps.core.models import Notification
        assert Notification.objects.filter(related_chat_room=party.chat_room).latest("id").content == "익명1님이 주문을 등록했어요"
