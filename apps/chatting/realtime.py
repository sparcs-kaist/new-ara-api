# 서버 -> 채팅방 소켓 알림. 보는 사람마다 다른 값이 있어 id 만 보내고, 클라이언트가 다시 조회한다
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.db import transaction

log = logging.getLogger(__name__)


def room_group_name(room_id: int) -> str:
    return f"chat_{room_id}"


def send_to_room(room_id: int, event: dict) -> None:
    if getattr(settings, "TEST", False):
        return

    def send():
        try:
            async_to_sync(get_channel_layer().group_send)(room_group_name(room_id), event)
        except Exception:
            log.exception("chat broadcast failed room=%s type=%s", room_id, event.get("type"))

    # 커밋 전에 보내면 다시 조회했을 때 데이터가 없다
    transaction.on_commit(send)


def broadcast_room_update(room_id: int, resource: str, change: str, object_id: int) -> None:
    send_to_room(room_id, {
        "type": "room_update",
        "payload": {"resource": resource, "change": change, "room_id": room_id, "data": {"id": object_id}},
    })


def broadcast_message_created(message) -> None:
    broadcast_room_update(message.chat_room_id, "messages", "created", message.id)


# 나가거나 내보내진 멤버의 소켓을 방에서 뺀다
def broadcast_member_removed(room_id: int, anon_number: int) -> None:
    send_to_room(room_id, {"type": "member_removed", "anon_number": anon_number})
