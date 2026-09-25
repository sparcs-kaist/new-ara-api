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
        # 알림함에는 남는다
        assert NotificationReadLog.objects.filter(read_by=self.user3).exists()
