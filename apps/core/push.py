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
        )
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
        )
    )


def _build_data(notification: "Notification") -> dict:
    data: dict = {"notification_id": str(notification.id)}
    if notification.related_chat_room_id:
        data["type"] = "chat"
        data["target_id"] = str(notification.related_chat_room_id)
    elif notification.related_comment_id:
        data["type"] = "comment"
        data["target_id"] = str(notification.related_comment_id)
        if notification.related_article_id:
            data["article_id"] = str(notification.related_article_id)
    elif notification.related_article_id:
        data["type"] = "article"
        data["target_id"] = str(notification.related_article_id)
    return data


# ---------- celery task 가 실제 발송할 때 호출하는 sync 진입점 ----------

def send_to_user_sync(
    user_id: int, title: str, body: str, data: Optional[dict] = None
) -> None:
    from apps.user.models import FCMToken
    tokens = list(
        FCMToken.objects.filter(user_id=user_id).values_list("token", flat=True)
    )
    _send_to_tokens(tokens, title, body, data or {})


def send_to_users_sync(
    user_ids: list[int], title: str, body: str, data: Optional[dict] = None
) -> None:
    from apps.user.models import FCMToken
    tokens = list(
        FCMToken.objects.filter(user_id__in=user_ids).values_list("token", flat=True)
    )
    _send_to_tokens(tokens, title, body, data or {})


# FCM 멀티캐스트 한 요청당 토큰 상한
_FCM_MULTICAST_LIMIT = 500

_INVALID_TOKEN_ERROR_CODES = frozenset({
    "registration-token-not-registered",
    "invalid-registration-token",
    "invalid-argument",
})


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
            code = getattr(err, "code", "") if err is not None else ""
            if code in _INVALID_TOKEN_ERROR_CODES:
                invalid_tokens.append(token)
            else:
                log.warning(
                    "FCM send failed token=%s… code=%s err=%r",
                    token[:12],
                    code,
                    err,
                )

    if invalid_tokens:
        from apps.user.models import FCMToken
        deleted, _ = FCMToken.objects.filter(token__in=invalid_tokens).delete()
        log.info("FCM cleaned up %d invalid tokens", deleted)
