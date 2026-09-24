"""서버 -> 채팅방 소켓 브로드캐스트

REST 로 상태가 바뀌면(투표, 정산, 배달 주문 등) 기존 room_update 형식으로 방에 알린다.
    {"resource": "messages" | "vote" | "payment" | "delivery",
     "change": "created" | "updated", "room_id": 1, "data": {"id": 1}}

보는 사람마다 다른 값(내 투표 등)이 있고 익명 방 정보가 새면 안 되므로 id 만 보낸다.
클라이언트는 id 로 다시 조회한다.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction

log = logging.getLogger(__name__)


def room_group_name(room_id: int) -> str:
    return f"chat_{room_id}"


def broadcast_room_update(room_id: int, resource: str, change: str, object_id: int) -> None:
    if getattr(settings, "TEST", False):
        return

    payload = {
        "resource": resource,
        "change": change,
        "room_id": room_id,
        "data": {"id": object_id},
    }

    def send():
        try:
            async_to_sync(get_channel_layer().group_send)(
                room_group_name(room_id),
                {"type": "room_update", "payload": payload},
            )
        except Exception:
            log.exception("채팅방 소켓 알림 실패 room=%s resource=%s", room_id, resource)

    # 커밋 전에 보내면 다시 조회했을 때 데이터가 없다
    transaction.on_commit(send)


def broadcast_message_created(message) -> None:
    broadcast_room_update(message.chat_room_id, "messages", "created", message.id)
