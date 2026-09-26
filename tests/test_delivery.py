from datetime import timedelta

import pytest
from django.utils import timezone

from apps.chatting.models import ChatMessage, ChatPaymentTarget
from apps.core.models import Notification
from apps.delivery.models import DeliveryParty, DeliveryPenalty, DeliveryStatus
from tests.conftest import RequestSetting, TestCase


@pytest.mark.usefixtures(
    "set_user_client", "set_user_client2", "set_user_client3", "set_user_client4"
)
class TestDelivery(TestCase, RequestSetting):
    # user = 방장, user2 / user3 = 참여자

    def open_party(self, min_order_amount=15000, price=8000, **extra):
        res = self.http_request(self.user, "post", "delivery", {
            "store_name": "아라식당 KAIST점",
            "place_name": "희망관 (W4)",
            "place_detail": "1층 로비",
            "min_order_amount": min_order_amount,
            "recruit_minutes": 30,
            "memo": "도착하면 채팅으로 알려드릴게요.",
            "price": price,
            "menu_name": "떡볶이",
            **extra,
        })
        assert res.status_code == 201, res.data
        return DeliveryParty.objects.get(pk=res.data["id"])

    def join_and_order(self, party, user, price, menu_name=""):
        assert self.http_request(user, "post", f"delivery/{party.id}/join").status_code == 200
        res = self.http_request(user, "post", f"delivery/{party.id}/orders", {"price": price, "menu_name": menu_name})
        assert res.status_code == 201, res.data
        return res.data

    def pass_deadline(self, party):
        DeliveryParty.objects.filter(pk=party.pk).update(deadline_at=timezone.now() - timedelta(seconds=1))
        DeliveryParty.sweep_deadlines()
        party.refresh_from_db()

    def pass_decision_deadline(self, party):
        DeliveryParty.objects.filter(pk=party.pk).update(decision_deadline_at=timezone.now() - timedelta(seconds=1))
        DeliveryParty.sweep_deadlines()
        party.refresh_from_db()


    def test_open_creates_room_with_host_order(self):
        party = self.open_party()
        assert party.chat_room.room_type == "DELIVERY"
        assert party.chat_room.chat_name_type == "ANONYMOUS"
        assert party.get_total_amount() == 8000

        res = self.http_request(self.user2, "get", "delivery")
        card = res.data["results"][0]
        assert card["total_amount"] == 8000
        assert card["participant_count"] == 1
        assert card["max_participants"] is None

        res = self.http_request(self.user2, "get", f"delivery/{party.id}")
        assert res.data["host_orders"] == [{"menu_name": "떡볶이", "price": 8000}]
        assert res.data["members"][0]["display_name"] == "방장"
        assert res.data["members"][0]["is_mine"] is False
        assert res.data["orders"] is None

    def test_menu_name_is_optional(self):
        party = self.open_party(menu_name="", order_link="https://baemin.com/group/abc")
        order = party.active_orders().get()
        assert order.menu_name == ""
        assert order.message.message_content == "[주문] 8,000원"

    def test_recruit_minutes_range(self):
        self.open_party(recruit_minutes=5)
        self.open_party(recruit_minutes=37)
        for minutes in (4, 61):
            res = self.http_request(self.user, "post", "delivery", {
                "store_name": "교촌", "place_name": "사랑관 (N1)", "min_order_amount": 10000,
                "recruit_minutes": minutes, "price": 5000,
            })
            assert res.status_code == 400

    def test_search(self):
        self.open_party()
        assert len(self.http_request(self.user2, "get", "delivery", querystring="search=희망관").data["results"]) == 1
        assert len(self.http_request(self.user2, "get", "delivery", querystring="search=피자").data["results"]) == 0


    def test_join_gives_anon_number_and_order_message(self):
        party = self.open_party()
        order = self.join_and_order(party, self.user2, 5000, "순대")
        assert order["orderer"]["display_name"] == "익명1"

        res = self.http_request(self.user2, "get", f"delivery/{party.id}")
        assert res.data["total_amount"] == 13000
        assert res.data["participant_count"] == 2
        assert len(res.data["orders"]) == 2

        messages = list(party.chat_room.message_set.order_by("id").values_list("message_type", flat=True))
        assert messages == ["DELIVERY_ORDER", "SYSTEM", "DELIVERY_ORDER"]

    def test_max_participants(self):
        party = self.open_party(max_participants=2)
        self.join_and_order(party, self.user2, 5000)
        res = self.http_request(self.user3, "post", f"delivery/{party.id}/join")
        assert res.status_code == 400
        assert res.data["detail"] == "정원이 다 찼어요."

    def test_order_requires_membership(self):
        party = self.open_party()
        res = self.http_request(self.user2, "post", f"delivery/{party.id}/orders", {"price": 1000})
        assert res.status_code == 403

    def test_leave_rules(self):
        party = self.open_party()
        order = self.join_and_order(party, self.user2, 5000)

        assert self.http_request(self.user, "post", f"delivery/{party.id}/leave").status_code == 400
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/leave").status_code == 400
        res = self.http_request(self.user2, "delete", f"delivery/{party.id}/orders/{order['id']}")
        assert res.status_code == 204
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/leave").status_code == 204

        self.http_request(self.user2, "post", f"delivery/{party.id}/join")
        assert party.get_membership(self.user2).anon_number == 1

    def test_chat_room_leave_is_blocked_for_delivery(self):
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        # 일반 채팅방 나가기로 주문 규칙을 우회할 수 없다
        res = self.http_request(self.user2, "post", f"chat/room/{party.chat_room_id}/leave")
        assert res.status_code == 400
        assert party.get_membership(self.user2) is not None


    def test_confirm_requires_min_amount(self):
        party = self.open_party(min_order_amount=15000)
        assert self.http_request(self.user, "post", f"delivery/{party.id}/confirm").status_code == 400

        self.join_and_order(party, self.user2, 7000)
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/confirm").status_code == 403
        res = self.http_request(self.user, "post", f"delivery/{party.id}/confirm")
        assert res.status_code == 200
        assert res.data["status"] == "ORDERED"

        res = self.http_request(self.user2, "post", f"delivery/{party.id}/orders", {"price": 1000})
        assert res.status_code == 400

    def test_cancel_without_other_orders_has_no_penalty(self):
        party = self.open_party()
        res = self.http_request(self.user, "post", f"delivery/{party.id}/cancel")
        assert res.data["status"] == "CANCELED"
        assert not DeliveryPenalty.objects.exists()

    def test_cancel_with_other_orders_gives_penalty(self):
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        self.http_request(self.user, "post", f"delivery/{party.id}/cancel")

        penalty = DeliveryPenalty.objects.get(user=self.user)
        assert timedelta(hours=2, minutes=59) < penalty.until - timezone.now() <= timedelta(hours=3)
        res = self.http_request(self.user, "post", "delivery", {
            "store_name": "교촌", "place_name": "사랑관 (N1)", "min_order_amount": 10000,
            "recruit_minutes": 10, "price": 5000,
        })
        assert res.status_code == 403

    def test_repeat_penalty_is_one_day(self):
        party = self.open_party()
        DeliveryPenalty.objects.create(
            user=self.user, party=party, until=timezone.now() - timedelta(hours=1),
            created_at=timezone.now() - timedelta(days=3),
        )
        penalty = DeliveryPenalty.give(self.user.id, party)
        assert penalty.until - timezone.now() > timedelta(hours=23)


    def test_deadline_min_not_met_then_cancel_has_no_penalty(self):
        party = self.open_party(min_order_amount=30000)
        self.join_and_order(party, self.user2, 5000)
        self.pass_deadline(party)
        assert party.status == DeliveryStatus.WAITING_DECISION.value
        assert party.decision_deadline_at is not None

        assert self.http_request(self.user3, "post", f"delivery/{party.id}/join").status_code == 400

        self.http_request(self.user, "post", f"delivery/{party.id}/cancel")
        party.refresh_from_db()
        assert party.status == "CANCELED"
        assert not DeliveryPenalty.objects.exists()

    def test_deadline_extend_reopens_recruiting(self):
        party = self.open_party(min_order_amount=30000)
        self.pass_deadline(party)
        res = self.http_request(self.user, "post", f"delivery/{party.id}/extend", {"minutes": 7})
        assert res.data["status"] == "RECRUITING"
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/join").status_code == 200

    def test_no_decision_with_min_met_is_auto_canceled_with_penalty(self):
        party = self.open_party(min_order_amount=10000)
        self.join_and_order(party, self.user2, 5000)
        self.pass_deadline(party)
        self.pass_decision_deadline(party)
        assert party.status == "CANCELED"
        assert party.cancel_reason == "NO_DECISION"
        assert DeliveryPenalty.objects.filter(user=self.user).exists()

    def test_no_decision_with_min_not_met_has_no_penalty(self):
        party = self.open_party(min_order_amount=30000)
        self.join_and_order(party, self.user2, 5000)
        self.pass_deadline(party)
        self.pass_decision_deadline(party)
        assert party.status == "CANCELED"
        assert not DeliveryPenalty.objects.exists()


    def test_arrival_notifies_everyone(self):
        party = self.open_party(min_order_amount=10000)
        self.join_and_order(party, self.user2, 5000)
        self.join_and_order(party, self.user3, 3000)
        self.http_request(self.user, "post", f"delivery/{party.id}/confirm")

        res = self.http_request(self.user, "post", f"delivery/{party.id}/arrive")
        assert res.data["status"] == "ARRIVED"
        assert ChatMessage.objects.filter(chat_room=party.chat_room, message_type="DELIVERY_ARRIVAL").exists()

        notification = Notification.objects.get(title="🛵 배달이 도착했어요")
        readers = set(notification.notification_read_log_set.values_list("read_by_id", flat=True))
        assert readers == {self.user2.id, self.user3.id}

    def test_payment_request_splits_fee_and_settles(self):
        party = self.open_party(min_order_amount=10000, price=8000)
        self.join_and_order(party, self.user2, 5000)
        self.http_request(self.user2, "post", f"delivery/{party.id}/orders", {"price": 1000})
        self.join_and_order(party, self.user3, 3000)
        self.http_request(self.user, "post", f"delivery/{party.id}/confirm")

        # 주문한 사람 3명 -> 배달비 3000원을 1000원씩
        res = self.http_request(self.user, "post", f"delivery/{party.id}/payment-request", {
            "bank_name": "토스뱅크", "account_number": "1000-1234-5678", "delivery_fee": 3000,
        })
        assert res.status_code == 201, res.data
        amounts = {t["user"]["display_name"]: t["amount"] for t in res.data["targets"]}
        assert amounts == {"익명1": 7000, "익명2": 4000}
        breakdown = {t["user"]["display_name"]: (t["order_amount"], t["delivery_fee_share"]) for t in res.data["targets"]}
        assert breakdown == {"익명1": (6000, 1000), "익명2": (3000, 1000)}

        assert self.http_request(self.user3, "post", f"delivery/{party.id}/leave").status_code == 400

        payment_id = res.data["id"]
        self.http_request(self.user3, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        assert self.http_request(self.user3, "post", f"delivery/{party.id}/leave").status_code == 204

        party.refresh_from_db()
        assert party.status == "ORDERED"
        self.http_request(self.user2, "patch", f"chat/payment/{payment_id}/paid", {"paid": True})
        party.refresh_from_db()
        assert party.status == "SETTLED"
        assert ChatPaymentTarget.objects.filter(request_id=payment_id, paid_at__isnull=True).count() == 0

        assert self.http_request(self.user, "post", f"delivery/{party.id}/leave").status_code == 204

    def test_delivery_room_cannot_be_blocked(self):
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        res = self.http_request(self.user2, "patch", f"chat/room/{party.chat_room_id}/block")
        assert res.status_code == 400
        res = self.http_request(self.user3, "patch", f"chat/room/{party.chat_room_id}/block", {"unblock": True})
        assert res.status_code == 400
        assert party.get_membership(self.user3) is None

    def test_host_alone_can_leave_after_order(self):
        party = self.open_party(min_order_amount=5000)
        self.http_request(self.user, "post", f"delivery/{party.id}/confirm")
        assert self.http_request(self.user, "post", f"delivery/{party.id}/leave").status_code == 204


    def test_edit_order_updates_card(self):
        party = self.open_party()
        order = self.join_and_order(party, self.user2, 5000, "순대")
        res = self.http_request(self.user2, "patch", f"delivery/{party.id}/orders/{order['id']}", {"price": 5500})
        assert res.status_code == 200
        assert res.data["price"] == 5500
        assert ChatMessage.objects.get(pk=order["message_id"]).message_content == "[주문] 순대 · 5,500원"
        res = self.http_request(self.user, "patch", f"delivery/{party.id}/orders/{order['id']}", {"price": 1})
        assert res.status_code == 403

    def test_host_updates_info(self):
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        res = self.http_request(self.user, "patch", f"delivery/{party.id}", {"order_link": "https://baemin.com/g/1", "memo": "1층"})
        assert res.status_code == 200
        assert res.data["order_link"] == "https://baemin.com/g/1"
        assert party.chat_room.message_set.filter(message_content="방장이 함께주문 링크를 올렸어요.").exists()
        res = self.http_request(self.user, "patch", f"delivery/{party.id}", {"max_participants": 1})
        assert res.status_code == 400
        assert self.http_request(self.user2, "patch", f"delivery/{party.id}", {"memo": "x"}).status_code == 403

    def test_kick_cancels_orders_and_blocks_rejoin(self):
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        res = self.http_request(self.user, "post", f"delivery/{party.id}/kick", {"anon_number": 1})
        assert res.status_code == 200
        assert res.data["total_amount"] == 8000
        assert party.get_membership(self.user2) is None
        res = self.http_request(self.user2, "post", f"delivery/{party.id}/join")
        assert res.status_code == 403

    def test_penalty_api(self):
        assert self.http_request(self.user, "get", "delivery/penalty").data["until"] is None
        party = self.open_party()
        self.join_and_order(party, self.user2, 5000)
        self.http_request(self.user, "post", f"delivery/{party.id}/cancel")
        res = self.http_request(self.user, "get", "delivery/penalty")
        assert res.data["until"] is not None
        assert res.data["reason"] == "HOST"
        assert res.data["duration_hours"] == 3

    def test_leave_unlocks_after_24h(self):
        party = self.open_party(min_order_amount=10000)
        self.join_and_order(party, self.user2, 5000)
        self.http_request(self.user, "post", f"delivery/{party.id}/confirm")
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/leave").status_code == 400
        DeliveryParty.objects.filter(pk=party.pk).update(ordered_at=timezone.now() - timedelta(hours=25))
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/leave").status_code == 204

    def confirmed_party_with_two_orders(self):
        # 방장(8000) / 익명1 user2(5000) / 익명2 user3(3000)
        party = self.open_party(min_order_amount=10000)
        self.join_and_order(party, self.user2, 5000)
        self.join_and_order(party, self.user3, 3000)
        self.http_request(self.user, "post", f"delivery/{party.id}/confirm")
        return party

    def request_delivery_payment(self, party):
        body = {"bank_name": "토스뱅크", "account_number": "1000-1", "delivery_fee": 0}
        return self.http_request(self.user, "post", f"delivery/{party.id}/payment-request", body)

    def test_resend_delivery_payment_when_nobody_paid(self):
        party = self.confirmed_party_with_two_orders()
        first = self.request_delivery_payment(party).data
        assert self.request_delivery_payment(party).status_code == 400

        self.http_request(self.user, "post", f"chat/payment/{first['id']}/cancel")
        assert self.http_request(self.user, "get", f"delivery/{party.id}").data["can_request_payment"] is True
        assert self.request_delivery_payment(party).status_code == 201

    def test_scenario_fix_one_amount_with_general_payment(self):
        # 갑(방장)이 배달 정산 → 병(user3)이 송금 → 을(user2) 금액이 틀려서 취소 → 을에게만 일반 정산
        party = self.confirmed_party_with_two_orders()
        first = self.request_delivery_payment(party).data
        self.http_request(self.user3, "patch", f"chat/payment/{first['id']}/paid", {"paid": True})
        self.http_request(self.user, "post", f"chat/payment/{first['id']}/cancel")

        assert self.http_request(self.user, "get", f"delivery/{party.id}").data["can_request_payment"] is False
        assert self.request_delivery_payment(party).status_code == 400

        res = self.http_request(self.user, "post", "chat/payment", {
            "chat_room": party.chat_room_id, "bank_name": "토스뱅크", "account_number": "1000-1",
            "targets": [{"anon_number": 1, "amount": 4500}],
        })
        assert res.status_code == 201

        # 병은 남은 정산이 없으니 나갈 수 있고, 을은 보내야 나갈 수 있다
        assert self.http_request(self.user3, "post", f"delivery/{party.id}/leave").status_code == 204
        assert self.http_request(self.user2, "post", f"delivery/{party.id}/leave").status_code == 400

        self.http_request(self.user2, "patch", f"chat/payment/{res.data['id']}/paid", {"paid": True})
        party.refresh_from_db()
        assert party.status == "SETTLED"

    def test_chat_room_has_delivery_party_id(self):
        party = self.open_party()
        res = self.http_request(self.user, "get", "chat/room")
        room = next(r for r in res.data["results"] if r["id"] == party.chat_room_id)
        assert room["delivery_party"] == party.id
