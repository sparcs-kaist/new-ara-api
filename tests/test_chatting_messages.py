import pytest

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
from tests.conftest import RequestSetting, TestCase, Utils


@pytest.fixture(scope="function")
def set_group_room(request):
    """user(방장), user2, user3 가 있는 그룹 채팅방. user4 는 참여하지 않음"""
    request.cls.room = ChatRoom.objects.create(
        room_title="그룹방",
        room_type=ChatRoomType.GROUP_DM.value,
        chat_name_type=ChatNameType.NICKNAME.value,
    )
    for user, role in [
        (request.cls.user, ChatUserRole.OWNER),
        (request.cls.user2, ChatUserRole.PARTICIPANT),
        (request.cls.user3, ChatUserRole.PARTICIPANT),
    ]:
        ChatRoomMemberShip.objects.create(chat_room=request.cls.room, user=user, role=role.value)


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_user_client3", "set_user_client4", "set_group_room"
)
class TestChatVote(TestCase, RequestSetting):
    def create_vote(self, max_choices=1, user=None):
        return self.http_request(user or self.user, "post", "chat/vote", {
            "chat_room": self.room.id,
            "title": "점심 뭐 먹지?",
            "options": ["카이마루", "서맛골", "교수회관"],
            "max_choices": max_choices,
        })

    def test_create_vote_makes_vote_message(self):
        res = self.create_vote()
        assert res.status_code == 201

        vote = ChatVote.objects.get(pk=res.data["id"])
        assert vote.message.message_type == "VOTE"
        assert vote.message.message_content == "[투표] 점심 뭐 먹지?"
        assert [o["text"] for o in res.data["options"]] == ["카이마루", "서맛골", "교수회관"]
        assert self.room.message_set.count() == 1

    def test_non_member_cannot_create_or_see_vote(self):
        assert self.create_vote(user=self.user4).status_code == 403

        vote_id = self.create_vote().data["id"]
        assert self.http_request(self.user4, "get", f"chat/vote/{vote_id}").status_code == 403

    def test_ballot_replaces_my_choices(self):
        res = self.create_vote(max_choices=2)
        vote_id = res.data["id"]
        a, b, c = [o["id"] for o in res.data["options"]]

        res = self.http_request(self.user2, "put", f"chat/vote/{vote_id}/ballot", {"option_ids": [a, b]})
        assert res.status_code == 200
        assert sorted(res.data["my_option_ids"]) == sorted([a, b])

        res = self.http_request(self.user2, "put", f"chat/vote/{vote_id}/ballot", {"option_ids": [c]})
        assert res.data["my_option_ids"] == [c]
        counts = {o["id"]: o["vote_count"] for o in res.data["options"]}
        assert counts == {a: 0, b: 0, c: 1}

        # 누가 투표했는지 보인다 (방 이름 표시 방식 = 닉네임)
        voters = next(o for o in res.data["options"] if o["id"] == c)["voters"]
        assert voters[0]["display_name"] == self.user2.profile.nickname

        # 빈 리스트면 취소
        res = self.http_request(self.user2, "put", f"chat/vote/{vote_id}/ballot", {"option_ids": []})
        assert res.data["voter_count"] == 0

        # 취소했던 선택지를 다시 골라도 된다 (soft delete 된 기록과 충돌하지 않음)
        res = self.http_request(self.user2, "put", f"chat/vote/{vote_id}/ballot", {"option_ids": [c]})
        assert res.status_code == 200
        assert res.data["my_option_ids"] == [c]

    def test_ballot_over_max_choices_is_rejected(self):
        res = self.create_vote(max_choices=1)
        a, b, _ = [o["id"] for o in res.data["options"]]
        res = self.http_request(self.user2, "put", f"chat/vote/{res.data['id']}/ballot", {"option_ids": [a, b]})
        assert res.status_code == 400

    def test_unlimited_choices(self):
        res = self.create_vote(max_choices=None)
        ids = [o["id"] for o in res.data["options"]]
        res = self.http_request(self.user2, "put", f"chat/vote/{res.data['id']}/ballot", {"option_ids": ids})
        assert res.status_code == 200
        assert len(res.data["my_option_ids"]) == 3

    def test_message_list_includes_vote_attachment(self):
        vote_id = self.create_vote().data["id"]
        res = self.http_request(self.user2, "get", "chat/message", querystring=f"chat_room={self.room.id}")
        assert res.status_code == 200
        message = res.data["results"][0]
        assert message["attachment"]["id"] == vote_id
        assert message["sender"]["display_name"] == self.user.profile.nickname

    def test_structured_types_cannot_be_sent_as_plain_message(self):
        res = self.http_request(self.user, "post", "chat/message", {
            "chat_room": self.room.id,
            "message_type": "VOTE",
            "message_content": "[Title]가짜 투표",
        })
        assert res.status_code == 400

    def test_vote_message_cannot_be_edited(self):
        vote = ChatVote.objects.get(pk=self.create_vote().data["id"])
        res = self.http_request(self.user, "put", f"chat/message/{vote.message_id}", {"message_content": "수정"})
        assert res.status_code == 400


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_user_client3", "set_user_client4", "set_group_room"
)
class TestChatPayment(TestCase, RequestSetting):
    def create_payment(self, targets=None):
        return self.http_request(self.user, "post", "chat/payment", {
            "chat_room": self.room.id,
            "bank_name": "카카오뱅크",
            "account_number": "3333-01-1234567",
            "targets": targets or [
                {"user": self.user2.id, "amount": 7000},
                {"user": self.user3.id, "amount": 5500},
            ],
        })

    def test_create_payment_request(self):
        res = self.create_payment()
        assert res.status_code == 201
        assert res.data["total_amount"] == 12500
        assert res.data["is_settled"] is False

        payment_request = ChatPaymentRequest.objects.get(pk=res.data["id"])
        # 계좌번호는 미리보기에 넣지 않는다
        assert "3333" not in payment_request.message.message_content

    def test_target_must_be_member(self):
        res = self.create_payment([{"user": self.user4.id, "amount": 1000}])
        assert res.status_code == 400

    def test_each_target_marks_paid(self):
        payment_id = self.create_payment().data["id"]

        # 대상자가 아니면 못 누른다
        res = self.http_request(self.user, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        assert res.status_code == 403

        self.http_request(self.user2, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        res = self.http_request(self.user3, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        assert res.status_code == 200
        assert res.data["is_settled"] is True

        res = self.http_request(self.user3, "patch", f"chat/payment/{payment_id}/paid", {"paid": False})
        assert res.data["is_settled"] is False


@pytest.mark.usefixtures("set_user_client", "set_user_client2", "set_user_client3")
class TestAnonymousRoom(TestCase, RequestSetting):
    def test_anon_numbers_and_masking(self):
        room = ChatRoom.objects.create(
            room_title="익명방",
            room_type=ChatRoomType.GROUP_DM.value,
            chat_name_type=ChatNameType.ANONYMOUS.value,
        )
        owner = ChatRoomMemberShip.objects.create(chat_room=room, user=self.user, role=ChatUserRole.OWNER.value)
        second = ChatRoomMemberShip.objects.create(chat_room=room, user=self.user2)
        third = ChatRoomMemberShip.objects.create(chat_room=room, user=self.user3)
        assert (owner.anon_number, second.anon_number, third.anon_number) == (0, 1, 2)
        assert owner.get_display_name() == "방장"
        assert second.get_display_name() == "익명1"

        # 나갔다 다시 들어와도 같은 번호
        second.delete()
        again = ChatRoomMemberShip.objects.create(chat_room=room, user=self.user2)
        assert again.anon_number == 1

        ChatMessage.create(chat_room=room, created_by=self.user2, message_type="TEXT", message_content="안녕")
        res = self.http_request(self.user3, "get", "chat/message", querystring=f"chat_room={room.id}")
        message = res.data["results"][0]
        assert message["created_by"] is None
        assert message["sender"]["display_name"] == "익명1"
        assert message["sender"]["is_mine"] is False


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_user_client3", "set_user_client4", "set_group_room"
)
class TestChatAccess(TestCase, RequestSetting):
    def test_message_list_without_room_only_shows_my_rooms(self):
        ChatMessage.create(chat_room=self.room, created_by=self.user, message_type="TEXT", message_content="비밀")
        res = self.http_request(self.user4, "get", "chat/message")
        assert res.status_code == 200
        assert res.data["results"] == []

        res = self.http_request(self.user2, "get", "chat/message")
        assert len(res.data["results"]) == 1

    def test_member_can_rename_room(self):
        res = self.http_request(self.user2, "patch", f"chat/room/{self.room.id}", {"room_title": "새 이름"})
        assert res.status_code == 200
        assert res.data["room_title"] == "새 이름"
        res = self.http_request(self.user4, "patch", f"chat/room/{self.room.id}", {"room_title": "x"})
        assert res.status_code == 403

    def test_cannot_join_room_by_unblock(self):
        res = self.http_request(self.user4, "patch", f"chat/room/{self.room.id}/block", {"unblock": True})
        assert res.status_code == 400
        assert not ChatRoomMemberShip.objects.filter(chat_room=self.room, user=self.user4).exists()


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_user_client3", "set_user_client4", "set_group_room"
)
class TestStructuredMessageEdit(TestCase, RequestSetting):
    def test_vote_can_be_deleted_by_author(self):
        res = self.http_request(self.user, "post", "chat/vote", {
            "chat_room": self.room.id, "title": "t", "options": ["a", "b"],
        })
        vote_id, message_id = res.data["id"], res.data["message_id"]
        assert self.http_request(self.user2, "delete", f"chat/message/{message_id}").status_code == 403
        assert self.http_request(self.user, "delete", f"chat/message/{message_id}").status_code == 200
        assert self.http_request(self.user, "get", f"chat/vote/{vote_id}").status_code == 404

    def test_payment_account_edit_before_anyone_paid(self):
        res = self.http_request(self.user, "post", "chat/payment", {
            "chat_room": self.room.id, "bank_name": "국민", "account_number": "1",
            "targets": [{"user": self.user2.id, "amount": 1000}],
        })
        payment_id = res.data["id"]
        res = self.http_request(self.user, "patch", f"chat/payment/{payment_id}", {"account_number": "2"})
        assert res.status_code == 200
        assert res.data["account_number"] == "2"
        assert self.http_request(self.user2, "patch", f"chat/payment/{payment_id}", {"account_number": "3"}).status_code == 403

        self.http_request(self.user2, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        assert self.http_request(self.user, "patch", f"chat/payment/{payment_id}", {"account_number": "4"}).status_code == 400
