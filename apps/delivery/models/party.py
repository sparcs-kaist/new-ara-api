import logging
import math
from collections import defaultdict
from datetime import timedelta
from enum import Enum

from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from ara.db.models import MetaDataModel
from ara.settings import MIN_TIME
from apps.chatting.models import (
    ChatMessage,
    ChatMessageType,
    ChatPaymentRequest,
    ChatRoom,
    ChatRoomMemberShip,
    ChatRoomPermission,
    ChatRoomType,
    ChatUserRole,
)
from apps.chatting.models.room import ChatNameType
from apps.chatting.realtime import (
    broadcast_member_removed,
    broadcast_message_created,
    broadcast_room_update,
)
from apps.delivery.models.order import DeliveryOrder
from apps.delivery.models.penalty import DeliveryPenalty

log = logging.getLogger(__name__)

# RECRUITING -(마감)-> WAITING_DECISION -(방장 확정)-> ORDERED -> ARRIVED -> SETTLED
# 최소 금액을 채우면 마감 전에도 바로 확정 가능. 연장하면 다시 RECRUITING
# 방장 취소 / 결정 시간 초과 -> CANCELED
class DeliveryStatus(str, Enum):
    RECRUITING = "RECRUITING" # 모집 중
    WAITING_DECISION = "WAITING_DECISION" # 마감됨. 방장이 주문 확정 / 연장 / 취소를 정해야 한다
    ORDERED = "ORDERED" # 방장이 주문함. 이후 주문 변경 불가
    ARRIVED = "ARRIVED" # 배달 도착
    SETTLED = "SETTLED" # 정산 완료
    CANCELED = "CANCELED" # 모집 취소

class DeliveryCancelReason(str, Enum):
    HOST = "HOST" # 방장이 취소
    NO_DECISION = "NO_DECISION" # 마감 후 방장이 정하지 않아 자동 취소

# 방 개설 / 연장 시간 (분). 이 범위의 아무 정수
MIN_RECRUIT_MINUTES = 5
MAX_RECRUIT_MINUTES = 60

# 확정 후 이 시간이 지나면 정산이 안 끝나도 나갈 수 있다 (방장 잠수 대비)
LEAVE_UNLOCK_AFTER = timedelta(hours=24)

OPEN_STATUSES = (DeliveryStatus.RECRUITING.value, DeliveryStatus.WAITING_DECISION.value)
FINISHED_STATUSES = (DeliveryStatus.SETTLED.value, DeliveryStatus.CANCELED.value)


class DeliveryActionError(Exception):
    """배달방 규칙상 할 수 없는 요청. 뷰에서 400 (forbidden 이면 403)"""
    def __init__(self, message: str, forbidden: bool = False):
        super().__init__(message)
        self.message = message
        self.forbidden = forbidden


# 함께 배달 방. 모집 정보는 여기, 대화는 연결된 채팅방(room_type=DELIVERY)
class DeliveryParty(MetaDataModel):
    chat_room = models.OneToOneField(
        verbose_name = "배달 채팅방",
        to = "chatting.ChatRoom",
        on_delete = models.CASCADE,
        related_name = "delivery_party",
    )
    host = models.ForeignKey(
        verbose_name = "방장",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "hosted_delivery_parties",
    )
    store_name = models.CharField(
        verbose_name = "식당",
        max_length = 100,
    )
    # 배달 받을 건물 (예: "희망관 (W4)") 과 상세 위치 (예: "1층 로비")
    place_name = models.CharField(
        verbose_name = "배달 받을 장소",
        max_length = 100,
    )
    place_detail = models.CharField(
        verbose_name = "상세 위치",
        max_length = 100,
        blank = True,
        default = "",
    )
    min_order_amount = models.PositiveIntegerField(
        verbose_name = "최소 주문 금액",
    )
    # null 이면 인원 제한 없음
    max_participants = models.PositiveSmallIntegerField(
        verbose_name = "최대 인원",
        null = True,
        blank = True,
        default = None,
    )
    # 처음 정한 모집 시간(분). 마감 후 방장 결정 대기 시간으로도 쓴다
    recruit_minutes = models.PositiveSmallIntegerField(
        verbose_name = "모집 시간(분)",
    )
    deadline_at = models.DateTimeField(
        verbose_name = "모집 마감 시각",
        db_index = True,
    )
    # 마감 후 이 시각까지 방장이 정하지 않으면 자동 취소
    decision_deadline_at = models.DateTimeField(
        verbose_name = "방장 결정 마감 시각",
        null = True,
        blank = True,
        default = None,
    )
    memo = models.TextField(
        verbose_name = "방장 메모",
        blank = True,
        default = "",
    )
    # 배민 함께주문 링크 (선택)
    order_link = models.URLField(
        verbose_name = "함께주문 링크",
        max_length = 500,
        blank = True,
        default = "",
    )
    status = models.CharField(
        verbose_name = "진행 상태",
        max_length = 20,
        choices = [(status.value, status.name) for status in DeliveryStatus],
        default = DeliveryStatus.RECRUITING.value,
        db_index = True,
    )
    cancel_reason = models.CharField(
        verbose_name = "취소 사유",
        max_length = 20,
        choices = [(reason.value, reason.name) for reason in DeliveryCancelReason],
        blank = True,
        default = "",
    )
    ordered_at = models.DateTimeField(verbose_name = "주문 확정 시각", null = True, blank = True, default = None)
    arrived_at = models.DateTimeField(verbose_name = "도착 시각", null = True, blank = True, default = None)
    settled_at = models.DateTimeField(verbose_name = "정산 완료 시각", null = True, blank = True, default = None)
    canceled_at = models.DateTimeField(verbose_name = "취소 시각", null = True, blank = True, default = None)

    payment_request = models.OneToOneField(
        verbose_name = "정산 요청",
        to = "chatting.ChatPaymentRequest",
        on_delete = models.SET_NULL,
        related_name = "delivery_party",
        null = True,
        blank = True,
        default = None,
    )

    # ---------- 조회 ----------

    @property
    def is_recruiting(self) -> bool:
        return self.status == DeliveryStatus.RECRUITING.value and timezone.now() < self.deadline_at

    def active_orders(self):
        return self.orders.filter(canceled_at__isnull=True)

    def get_total_amount(self) -> int:
        return self.active_orders().aggregate(total=Sum("price"))["total"] or 0

    def is_min_met(self) -> bool:
        return self.get_total_amount() >= self.min_order_amount

    def has_other_orders(self) -> bool:
        return self.active_orders().exclude(user_id=self.host_id).exists()

    def get_participant_count(self) -> int:
        return ChatRoomMemberShip.objects.filter(chat_room_id=self.chat_room_id).count()

    def get_membership(self, user):
        return ChatRoomMemberShip.objects.filter(chat_room_id=self.chat_room_id, user=user).first()

    # 정산 메시지를 지우면 None (다시 요청할 수 있다)
    @property
    def current_payment_request(self):
        request = self.payment_request
        if request is None or request.message.deleted_at != MIN_TIME:
            return None
        return request

    @property
    def is_leave_unlocked(self) -> bool:
        return bool(self.ordered_at and timezone.now() >= self.ordered_at + LEAVE_UNLOCK_AFTER)

    # ---------- 방 만들기 ----------

    @classmethod
    @transaction.atomic
    def open(cls, host, *, store_name, place_name, min_order_amount, recruit_minutes, price,
             menu_name="", place_detail="", max_participants=None, memo="", order_link=""):
        penalty_until = DeliveryPenalty.active_until(host)
        if penalty_until:
            until = timezone.localtime(penalty_until).strftime("%m월 %d일 %H:%M")
            raise DeliveryActionError(f"{until}까지 함께 배달 방을 만들 수 없어요.", forbidden=True)

        chat_room = ChatRoom.objects.create(
            room_title=store_name,
            room_type=ChatRoomType.DELIVERY.value,
            chat_name_type=ChatNameType.ANONYMOUS.value,
        )
        ChatRoomPermission.objects.create(
            chat_room=chat_room,
            entrance_permission="ALL",
            invite_permission="OWNER",
            message_permission="PARTICIPANT",
        )
        ChatRoomMemberShip.objects.create(
            chat_room=chat_room,
            user=host,
            role=ChatUserRole.OWNER.value,
        )

        party = cls.objects.create(
            chat_room=chat_room,
            host=host,
            store_name=store_name,
            place_name=place_name,
            place_detail=place_detail,
            min_order_amount=min_order_amount,
            max_participants=max_participants,
            recruit_minutes=recruit_minutes,
            deadline_at=timezone.now() + timedelta(minutes=recruit_minutes),
            memo=memo,
            order_link=order_link,
        )
        # 방장도 자기 주문을 넣고 시작한다
        party.add_order(host, price=price, menu_name=menu_name)
        return party

    # ---------- 참여자 ----------

    @transaction.atomic
    def join(self, user):
        self.lock_row()
        if not self.is_recruiting:
            raise DeliveryActionError("모집이 끝난 방이에요.")
        if self.get_membership(user):
            raise DeliveryActionError("이미 참여 중인 방이에요.")
        if self.max_participants and self.get_participant_count() >= self.max_participants:
            raise DeliveryActionError("정원이 다 찼어요.")

        # 나갔다 다시 들어오면 예전 멤버십을 되살린다 (익명 번호 유지)
        membership = ChatRoomMemberShip.objects.queryset_with_deleted.filter(
            chat_room_id=self.chat_room_id,
            user=user,
        ).order_by("-id").first()
        if membership and membership.role == ChatUserRole.BLOCKED.value:
            raise DeliveryActionError("방장이 내보낸 방이라 다시 들어갈 수 없어요.", forbidden=True)
        if membership:
            membership.deleted_at = MIN_TIME
            membership.role = ChatUserRole.PARTICIPANT.value
            membership.save()
        else:
            membership = ChatRoomMemberShip.objects.create(
                chat_room_id=self.chat_room_id,
                user=user,
                role=ChatUserRole.PARTICIPANT.value,
            )

        self.send_system_message(f"{membership.get_display_name()}님이 참여했어요.")
        self.broadcast_update()
        return membership

    @transaction.atomic
    def leave(self, user):
        self.lock_row()
        membership = self.get_membership(user)
        if membership is None:
            raise DeliveryActionError("참여 중인 방이 아니에요.")

        if self.status not in FINISHED_STATUSES and not self.is_leave_unlocked:
            has_orders = self.active_orders().filter(user=user).exists()
            if user.id == self.host_id:
                if self.status in OPEN_STATUSES:
                    raise DeliveryActionError("방장은 나갈 수 없어요. 모집을 취소해주세요.")
                # 다른 사람 주문이 없으면 받을 돈도 없으니 나갈 수 있다
                if self.has_other_orders():
                    raise DeliveryActionError("정산이 끝나야 나갈 수 있어요.")
            elif has_orders and self.status in OPEN_STATUSES:
                raise DeliveryActionError("주문을 취소한 뒤 나갈 수 있어요.")
            elif has_orders and not self.has_paid(user):
                raise DeliveryActionError("정산을 마쳐야 나갈 수 있어요.")

        name = membership.get_display_name()
        membership.delete()
        if self.status not in FINISHED_STATUSES:
            self.send_system_message(f"{name}님이 나갔어요.")
        broadcast_member_removed(self.chat_room_id, membership.anon_number)
        self.broadcast_update()

    @transaction.atomic
    def kick(self, user, anon_number: int):
        self.lock_row()
        self.check_host(user)
        target = ChatRoomMemberShip.objects.filter(
            chat_room_id=self.chat_room_id, anon_number=anon_number,
        ).first()
        if target is None:
            raise DeliveryActionError("방에 없는 참여자예요.")
        if target.user_id == self.host_id:
            raise DeliveryActionError("방장은 내보낼 수 없어요.")

        orders = list(self.active_orders().filter(user_id=target.user_id))
        if orders and self.status not in OPEN_STATUSES:
            raise DeliveryActionError("주문을 확정한 뒤에는 주문한 사람을 내보낼 수 없어요.")

        now = timezone.now()
        for order in orders:
            order.canceled_at = now
            order.save()
            broadcast_room_update(self.chat_room_id, "messages", "updated", order.message_id)

        name = target.get_display_name()
        # BLOCKED 로 남겨서 다시 참여하지 못하게 한다
        target.role = ChatUserRole.BLOCKED.value
        target.delete()

        self.send_system_message(f"방장이 {name}님을 내보냈어요.")
        broadcast_member_removed(self.chat_room_id, anon_number)
        self.broadcast_update()

    # 방장이 고칠 수 있는 정보 (모집 중일 때만)
    @transaction.atomic
    def update_info(self, user, **fields):
        self.lock_row()
        self.check_host(user)
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("모집 중일 때만 방 정보를 고칠 수 있어요.")

        max_participants = fields.get("max_participants")
        if max_participants is not None and max_participants < self.get_participant_count():
            raise DeliveryActionError("지금 인원보다 적게 정할 수 없어요.")

        link_added = bool(fields.get("order_link")) and fields["order_link"] != self.order_link
        for name, value in fields.items():
            setattr(self, name, value)
        self.save()

        if link_added:
            self.send_system_message("방장이 함께주문 링크를 올렸어요.")
        self.broadcast_update()

    # ---------- 주문 ----------

    @transaction.atomic
    def place_order(self, user, *, price, menu_name=""):
        self.lock_row()
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("지금은 주문을 넣을 수 없어요.")
        if self.get_membership(user) is None:
            raise DeliveryActionError("방에 참여한 뒤 주문할 수 있어요.", forbidden=True)
        return self.add_order(user, price=price, menu_name=menu_name)

    @transaction.atomic
    def cancel_order(self, order, user):
        self.lock_row()
        if order.party_id != self.id or order.user_id != user.id:
            raise DeliveryActionError("내 주문만 취소할 수 있어요.", forbidden=True)
        if order.is_canceled:
            raise DeliveryActionError("이미 취소된 주문이에요.")
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("주문이 확정돼서 취소할 수 없어요.")

        order.canceled_at = timezone.now()
        order.save()

        name = self.get_membership(user).get_display_name()
        self.send_system_message(f"{name}님이 주문을 취소했어요. ({order.summary})")
        broadcast_room_update(self.chat_room_id, "messages", "updated", order.message_id)
        self.broadcast_update()

    @transaction.atomic
    def edit_order(self, order, user, **fields):
        self.lock_row()
        if order.party_id != self.id or order.user_id != user.id:
            raise DeliveryActionError("내 주문만 고칠 수 있어요.", forbidden=True)
        if order.is_canceled:
            raise DeliveryActionError("취소된 주문이에요.")
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("주문이 확정돼서 고칠 수 없어요.")

        for name, value in fields.items():
            setattr(order, name, value)
        order.save()
        # 채팅방 주문 카드 미리보기도 같이 바꾼다
        order.message.message_content = f"[주문] {order.summary}"
        order.message.save()

        broadcast_room_update(self.chat_room_id, "messages", "updated", order.message_id)
        self.broadcast_update()
        return order

    def add_order(self, user, *, price, menu_name=""):
        message = ChatMessage.create(
            chat_room=self.chat_room,
            created_by=user,
            message_type=ChatMessageType.DELIVERY_ORDER.value,
            message_content=f"[주문] {DeliveryOrder.make_summary(menu_name, price)}",
        )
        order = DeliveryOrder.objects.create(
            message=message,
            party=self,
            user=user,
            menu_name=menu_name,
            price=price,
        )
        broadcast_message_created(message)
        self.broadcast_update()
        return order

    # ---------- 방장 ----------

    @transaction.atomic
    def confirm_order(self, user):
        self.lock_row()
        self.check_host(user)
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("지금은 주문을 확정할 수 없어요.")
        if not self.is_min_met():
            raise DeliveryActionError("최소 주문 금액을 채워야 주문할 수 있어요.")

        self.status = DeliveryStatus.ORDERED.value
        self.ordered_at = timezone.now()
        self.decision_deadline_at = None
        self.save()

        content = "방장이 주문을 확정했어요. 이제 주문을 바꿀 수 없어요."
        self.send_system_message(content)
        self.notify_members("주문이 확정됐어요", f"{self.store_name} · {content}", exclude_host=True)
        self.broadcast_update()

    @transaction.atomic
    def extend(self, user, minutes: int):
        self.lock_row()
        self.check_host(user)
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("지금은 모집을 연장할 수 없어요.")

        self.deadline_at = max(timezone.now(), self.deadline_at) + timedelta(minutes=minutes)
        self.status = DeliveryStatus.RECRUITING.value
        self.decision_deadline_at = None
        self.save()

        self.send_system_message(f"모집 시간이 {minutes}분 늘어났어요.")
        self.broadcast_update()

    @transaction.atomic
    def cancel(self, user):
        self.lock_row()
        self.check_host(user)
        if self.status not in OPEN_STATUSES:
            raise DeliveryActionError("주문을 확정한 뒤에는 취소할 수 없어요.")

        # 마감까지 최소 금액을 못 채운 경우는 패널티 없음
        min_failed = self.status == DeliveryStatus.WAITING_DECISION.value and not self.is_min_met()
        penalize = self.has_other_orders() and not min_failed

        self.mark_canceled(DeliveryCancelReason.HOST)
        content = "방장이 모집을 취소했어요."
        self.send_system_message(content)
        self.notify_members("함께 배달이 취소됐어요", f"{self.store_name} · {content}", exclude_host=True)
        if penalize:
            DeliveryPenalty.give(self.host_id, self)
        self.broadcast_update()

    @transaction.atomic
    def arrive(self, user):
        self.lock_row()
        self.check_host(user)
        if self.status != DeliveryStatus.ORDERED.value:
            raise DeliveryActionError("주문을 확정한 뒤에 도착 알림을 보낼 수 있어요.")

        self.status = DeliveryStatus.ARRIVED.value
        self.arrived_at = timezone.now()
        self.save()

        # 푸시는 DELIVERY_ARRIVAL 메시지 알림에서 보낸다
        message = ChatMessage.create(
            chat_room=self.chat_room,
            created_by=user,
            message_type=ChatMessageType.DELIVERY_ARRIVAL.value,
            message_content="배달이 도착했어요! 🛵",
        )
        broadcast_message_created(message)
        self.broadcast_update()
        return message

    # 1인 금액 = 내 주문 합계 + 배달비 / 주문한 사람 수 (올림)
    @transaction.atomic
    def request_payment(self, user, *, bank_name, account_number, delivery_fee=0):
        self.lock_row()
        self.check_host(user)
        if self.status not in (DeliveryStatus.ORDERED.value, DeliveryStatus.ARRIVED.value):
            raise DeliveryActionError("주문을 확정한 뒤에 정산을 요청할 수 있어요.")
        if self.current_payment_request:
            raise DeliveryActionError("이미 정산을 요청했어요. 잘못 보냈다면 정산 메시지를 지우고 다시 보내주세요.")

        subtotals = defaultdict(int)
        users = {}
        for order in self.active_orders().select_related("user"):
            subtotals[order.user_id] += order.price
            users[order.user_id] = order.user

        fee_share = math.ceil(delivery_fee / len(subtotals)) if subtotals else 0
        targets = [
            (users[user_id], subtotal + fee_share)
            for user_id, subtotal in subtotals.items()
            if user_id != self.host_id
        ]
        if not targets:
            raise DeliveryActionError("정산할 다른 참여자가 없어요.")

        self.payment_request = ChatPaymentRequest.create_with_message(
            chat_room=self.chat_room,
            created_by=user,
            bank_name=bank_name,
            account_number=account_number,
            targets=targets,
        )
        self.save()
        broadcast_message_created(self.payment_request.message)
        self.broadcast_update()
        return self.payment_request

    # 정산 대상자가 모두 송금 완료를 누르면 호출된다 (signals 참고)
    @transaction.atomic
    def settle_if_paid(self):
        self.lock_row()
        if self.status not in (DeliveryStatus.ORDERED.value, DeliveryStatus.ARRIVED.value):
            return
        request = self.current_payment_request
        if request is None or not request.is_settled:
            return

        self.status = DeliveryStatus.SETTLED.value
        self.settled_at = timezone.now()
        self.save()
        self.send_system_message("정산이 끝났어요. 이제 방을 나갈 수 있어요.")
        self.broadcast_update()

    # ---------- 마감 처리 (celery 에서 1분마다) ----------

    @classmethod
    def sweep_deadlines(cls):
        now = timezone.now()
        due_recruiting = cls.objects.filter(
            status=DeliveryStatus.RECRUITING.value, deadline_at__lte=now,
        ).values_list("pk", flat=True)
        due_decision = cls.objects.filter(
            status=DeliveryStatus.WAITING_DECISION.value, decision_deadline_at__lte=now,
        ).values_list("pk", flat=True)

        for pk in list(due_recruiting):
            try:
                cls.objects.get(pk=pk).close_recruiting()
            except Exception:
                log.exception("배달방 모집 마감 처리 실패 party=%s", pk)
        for pk in list(due_decision):
            try:
                cls.objects.get(pk=pk).expire_decision()
            except Exception:
                log.exception("배달방 결정 시간 초과 처리 실패 party=%s", pk)

    @transaction.atomic
    def close_recruiting(self):
        self.lock_row()
        if self.status != DeliveryStatus.RECRUITING.value or timezone.now() < self.deadline_at:
            return

        self.status = DeliveryStatus.WAITING_DECISION.value
        self.decision_deadline_at = timezone.now() + timedelta(minutes=self.recruit_minutes)
        self.save()

        if self.is_min_met():
            content = f"모집이 마감됐어요. 방장님, {self.recruit_minutes}분 안에 주문을 확정해주세요."
        else:
            content = "최소 주문 금액을 채우지 못했어요. 방장님, 모집을 연장하거나 취소해주세요."
        self.send_system_message(content)
        self.notify_members("함께 배달 모집이 마감됐어요", f"{self.store_name} · {content}", only_host=True)
        self.broadcast_update()

    @transaction.atomic
    def expire_decision(self):
        self.lock_row()
        if self.status != DeliveryStatus.WAITING_DECISION.value or timezone.now() < self.decision_deadline_at:
            return

        # 최소 금액을 채웠는데 주문하지 않은 경우만 패널티
        penalize = self.has_other_orders() and self.is_min_met()

        self.mark_canceled(DeliveryCancelReason.NO_DECISION)
        content = "방장이 정하지 않아 모집이 자동으로 취소됐어요."
        self.send_system_message(content)
        self.notify_members("함께 배달이 취소됐어요", f"{self.store_name} · {content}")
        if penalize:
            DeliveryPenalty.give(self.host_id, self)
        self.broadcast_update()

    # ---------- 공통 ----------

    def lock_row(self):
        # 동시에 들어온 요청(정원, 상태 변경)을 한 줄로 세운다
        list(DeliveryParty.objects.select_for_update().filter(pk=self.pk).values_list("pk", flat=True))
        self.refresh_from_db()

    def check_host(self, user):
        if user.id != self.host_id:
            raise DeliveryActionError("방장만 할 수 있어요.", forbidden=True)

    def has_paid(self, user) -> bool:
        request = self.current_payment_request
        if request is None:
            return False
        return request.targets.filter(user=user, paid_at__isnull=False).exists()

    def mark_canceled(self, reason: DeliveryCancelReason):
        self.status = DeliveryStatus.CANCELED.value
        self.cancel_reason = reason.value
        self.canceled_at = timezone.now()
        self.decision_deadline_at = None
        self.save()

    def send_system_message(self, content: str):
        message = ChatMessage.create_system(self.chat_room, content)
        broadcast_message_created(message)
        return message

    def notify_members(self, title: str, content: str, exclude_host=False, only_host=False):
        from apps.core.models import Notification

        if only_host:
            user_ids = [self.host_id]
        else:
            memberships = ChatRoomMemberShip.objects.filter(chat_room_id=self.chat_room_id).exclude(
                role__in=[ChatUserRole.BLOCKED.value, ChatUserRole.BLOCKER.value],
            )
            if exclude_host:
                memberships = memberships.exclude(user_id=self.host_id)
            user_ids = list(memberships.values_list("user_id", flat=True))
        Notification.notify_chat_room_event(self.chat_room, title, content, user_ids)

    def broadcast_update(self):
        broadcast_room_update(self.chat_room_id, "delivery", "updated", self.id)
