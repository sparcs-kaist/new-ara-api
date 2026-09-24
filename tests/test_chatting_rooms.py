import pytest

from apps.chatting.models import (
    ChatRoom,
    ChatRoomInvitation,
    ChatRoomMemberShip,
    ChatRoomPermission,
    ChatRoomType,
    ChatUserRole,
)
from apps.chatting.models.room import ChatNameType
from tests.conftest import RequestSetting, TestCase


def make_room(room_type, members, name_type=ChatNameType.ANONYMOUS):
    """members : [(user, role), ...] 순서대로 들어온다 (첫 번째가 방장이면 0번)"""
    room = ChatRoom.objects.create(
        room_title="방", room_type=room_type.value, chat_name_type=name_type.value,
    )
    ChatRoomPermission.objects.create(chat_room=room)
    for user, role in members:
        ChatRoomMemberShip.objects.create(chat_room=room, user=user, role=role.value)
    return room


@pytest.mark.usefixtures("set_user_client", "set_user_client2", "set_user_client3")
class TestGroupChat(TestCase, RequestSetting):
    """단톡방: 모두 같은 멤버. 방장 권한이 없다"""

    def setUp(self):
        self.room = make_room(ChatRoomType.GROUP_DM, [
            (self.user, ChatUserRole.OWNER),
            (self.user2, ChatUserRole.PARTICIPANT),
        ])

    def test_anyone_can_rename(self):
        res = self.http_request(self.user2, "patch", f"chat/room/{self.room.id}", {"room_title": "새 이름"})
        assert res.status_code == 200
        assert res.data["room_title"] == "새 이름"
        assert self.room.message_set.filter(message_type="SYSTEM").exists()

    def test_non_member_cannot_rename(self):
        res = self.http_request(self.user3, "patch", f"chat/room/{self.room.id}", {"room_title": "x"})
        assert res.status_code == 403

    def test_no_kick_or_admin(self):
        assert self.http_request(self.user, "post", f"chat/room/{self.room.id}/kick", {"anon_number": 1}).status_code == 400
        res = self.http_request(self.user, "patch", f"chat/room/{self.room.id}/role", {"anon_number": 1, "role": "ADMIN"})
        assert res.status_code == 400

    def test_creator_can_leave_but_not_delete(self):
        assert self.http_request(self.user, "delete", f"chat/room/{self.room.id}").status_code == 400
        assert self.http_request(self.user, "post", f"chat/room/{self.room.id}/leave").status_code == 204


@pytest.mark.usefixtures("set_user_client", "set_user_client2", "set_user_client3", "set_user_client4")
class TestOpenChat(TestCase, RequestSetting):
    """오픈채팅: 방장(0) / user2(익명1) / user3(익명2)"""

    def setUp(self):
        self.room = make_room(ChatRoomType.OPEN_CHAT, [
            (self.user, ChatUserRole.OWNER),
            (self.user2, ChatUserRole.PARTICIPANT),
            (self.user3, ChatUserRole.PARTICIPANT),
        ])

    def test_only_owner_or_admin_can_rename(self):
        assert self.http_request(self.user2, "patch", f"chat/room/{self.room.id}", {"room_title": "x"}).status_code == 403
        assert self.http_request(self.user, "patch", f"chat/room/{self.room.id}", {"room_title": "x"}).status_code == 200

    def test_owner_must_transfer_before_leaving(self):
        assert self.http_request(self.user, "post", f"chat/room/{self.room.id}/leave").status_code == 403

        res = self.http_request(self.user, "post", f"chat/room/{self.room.id}/owner", {"anon_number": 1})
        assert res.status_code == 200
        old_owner = ChatRoomMemberShip.objects.get(chat_room=self.room, user=self.user)
        new_owner = ChatRoomMemberShip.objects.get(chat_room=self.room, user=self.user2)
        assert new_owner.role == "OWNER"
        assert old_owner.role == "PARTICIPANT"
        # 전 방장이 "익명0" 으로 보이지 않는다
        assert old_owner.anon_number == 3
        assert self.http_request(self.user, "post", f"chat/room/{self.room.id}/leave").status_code == 204

    def test_admin_can_kick_participant_but_not_admin(self):
        self.http_request(self.user, "patch", f"chat/room/{self.room.id}/role", {"anon_number": 1, "role": "ADMIN"})
        assert ChatRoomMemberShip.objects.get(chat_room=self.room, user=self.user2).role == "ADMIN"

        # 참여자는 못 내보낸다
        assert self.http_request(self.user3, "post", f"chat/room/{self.room.id}/kick", {"anon_number": 1}).status_code == 403
        # 관리자는 방장을 못 내보낸다
        assert self.http_request(self.user2, "post", f"chat/room/{self.room.id}/kick", {"anon_number": 0}).status_code == 403
        # 관리자가 참여자를 내보낸다
        assert self.http_request(self.user2, "post", f"chat/room/{self.room.id}/kick", {"anon_number": 2}).status_code == 200
        assert ChatRoomMemberShip.get_active(self.room, self.user3) is None

    def test_kicked_member_cannot_rejoin_by_invitation(self):
        self.http_request(self.user, "post", f"chat/room/{self.room.id}/kick", {"anon_number": 2})
        invitation = ChatRoomInvitation.objects.create(
            invited_room=self.room, invitation_to=self.user3, invitation_from=self.user,
        )
        res = self.http_request(self.user3, "post", f"chat/invitation/{invitation.id}/accept")
        assert res.status_code == 400
        assert ChatRoomMemberShip.get_active(self.room, self.user3) is None


@pytest.mark.usefixtures("set_user_client", "set_user_client2")
class TestDMRoom(TestCase, RequestSetting):
    def test_dm_cannot_be_renamed(self):
        room = make_room(ChatRoomType.DM, [
            (self.user, ChatUserRole.PARTICIPANT),
            (self.user2, ChatUserRole.PARTICIPANT),
        ], name_type=ChatNameType.NICKNAME)
        res = self.http_request(self.user, "patch", f"chat/room/{room.id}", {"room_title": "x"})
        assert res.status_code == 400
