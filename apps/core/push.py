"""FCM push notification helpers.

진입점은 두 개:
- `enqueue_push_for_notification(notification, user_id)` — 단일 유저 알림.
- `enqueue_push_for_notification_to_users(notification, user_ids)` — 여러 유저 (채팅).

둘 다 `transaction.on_commit` 안에서 celery task 를 enqueue 하므로, 호출하는
쪽 트랜잭션이 먼저 커밋되어야 push 가 발사된다 (DB 에 row 가 없는 상태로
fcm 가 도달하는 race 방지).

FCM payload data 컨벤션 (frontend 와 약속):
- `notification_id`: backend Notification.id (str)
- `type`: "article" | "comment" | "chat"
- `target_id`: 관련 엔티티 id (article_id / comment_id / chat_room_id)
- `article_id`: type=="comment" 일 때만, 부모 article id
- `route`: 앱이 여는 웹뷰 경로 ("/web_view/Chat/<room_id>" | "/web_view/Post/<article_id>")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Iterable, Optional

from django.conf import settings
from django.db import transaction

if TYPE_CHECKING:
    from apps.core.models.notification import Notification

log = logging.getLogger(__name__)


def enqueue_push_for_notification(notification: "Notification", user_id: int) -> None:
    if not getattr(settings, "FCM_ENABLED", False):
        return

    title = notification.title
    body = (notification.content or "")[:200]
    data = _build_data(notification)

    from apps.core.management.tasks import send_push_to_user

    transaction.on_commit(
        lambda: send_push_to_user.delay(
            user_id=user_id, title=title, body=body, data=data
        ),
        # broker 오류가 이미 커밋된 요청을 500 으로 만들지 않게
        robust=True,
    )


def enqueue_push_for_notification_to_users(
    notification: "Notification", user_ids: Iterable[int]
) -> None:
    if not getattr(settings, "FCM_ENABLED", False):
        return

    user_ids = [uid for uid in user_ids if uid is not None]
    if not user_ids:
        return

    title = notification.title
    body = (notification.content or "")[:200]
    data = _build_data(notification)

    from apps.core.management.tasks import send_push_to_users

    transaction.on_commit(
        lambda: send_push_to_users.delay(
            user_ids=user_ids, title=title, body=body, data=data
        ),
        robust=True,
    )


def _build_data(notification: "Notification") -> dict:
    data: dict = {"notification_id": str(notification.id)}
    if notification.related_chat_room_id:
        data["type"] = "chat"
        data["target_id"] = str(notification.related_chat_room_id)
        data["route"] = f"/web_view/Chat/{notification.related_chat_room_id}"
    elif notification.related_comment_id:
        data["type"] = "comment"
        data["target_id"] = str(notification.related_comment_id)
        if notification.related_article_id:
            data["article_id"] = str(notification.related_article_id)
            data["route"] = f"/web_view/Post/{notification.related_article_id}"
    elif notification.related_article_id:
        data["type"] = "article"
        data["target_id"] = str(notification.related_article_id)
        data["route"] = f"/web_view/Post/{notification.related_article_id}"
    return data


# ---------- celery task 가 실제 발송할 때 호출하는 sync 진입점 ----------

def send_to_user_sync(
    user_id: int, title: str, body: str, data: Optional[dict] = None
) -> None:
    from apps.user.models import FCMToken
    tokens = list(
        FCMToken.objects.filter(user_id=user_id, user__is_active=True).values_list(
            "token", flat=True
        )
    )
    _send_to_tokens(tokens, title, body, data or {})


def send_to_users_sync(
    user_ids: list[int], title: str, body: str, data: Optional[dict] = None
) -> None:
    from apps.user.models import FCMToken
    tokens = list(
        FCMToken.objects.filter(
            user_id__in=user_ids, user__is_active=True
        ).values_list("token", flat=True)
    )
    _send_to_tokens(tokens, title, body, data or {})


# send_each_for_multicast 는 토큰 하나당 스레드/HTTP 요청 하나를 쓴다
_FCM_MULTICAST_LIMIT = 50


def _send_to_tokens(
    tokens: list[str], title: str, body: str, data: dict
) -> None:
    if not tokens or not getattr(settings, "FCM_ENABLED", False):
        return

    from firebase_admin import messaging
    from firebase_admin.exceptions import FirebaseError

    # FCM 은 모든 data 값을 string 으로 요구
    string_data = {k: str(v) for k, v in data.items()}

    invalid_tokens: list[str] = []
    for i in range(0, len(tokens), _FCM_MULTICAST_LIMIT):
        chunk = tokens[i : i + _FCM_MULTICAST_LIMIT]
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=string_data,
            tokens=chunk,
        )
        try:
            response = messaging.send_each_for_multicast(message)
        except FirebaseError as e:
            log.warning("FCM multicast failed for chunk of %d: %r", len(chunk), e)
            continue

        for token, resp in zip(chunk, response.responses):
            if resp.success:
                continue
            err = resp.exception
            # UnregisteredError 만 토큰 자체가 죽은 경우다. SENDER_ID_MISMATCH 는
            # 서버 설정 오류일 수 있어 지우면 전체 토큰이 날아간다.
            if isinstance(err, messaging.UnregisteredError):
                invalid_tokens.append(token)
            else:
                log.warning("FCM send failed token=%s… err=%r", token[:12], err)

    if invalid_tokens:
        from apps.user.models import FCMToken
        deleted, _ = FCMToken.objects.filter(token__in=invalid_tokens).delete()
        log.info("FCM cleaned up %d invalid tokens", deleted)
