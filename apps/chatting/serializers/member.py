from apps.chatting.models.membership_room import ChatRoomMemberShip
from apps.chatting.models.room import ChatNameType


def member_directory(serializer, chat_room) -> dict:
    """
    채팅방의 {user_id: membership}. 나간 멤버도 포함 (예전 메시지 작성자 표시용)
    응답 하나를 만드는 동안 context 에 캐시한다
    """
    cache = serializer.context.setdefault("member_directory", {})
    if chat_room.id not in cache:
        memberships = ChatRoomMemberShip.objects.queryset_with_deleted.filter(
            chat_room=chat_room,
        ).select_related("user__profile", "chat_room").order_by("id")
        # 같은 유저가 여러 번 들어온 경우 가장 최근 멤버십이 남는다
        cache[chat_room.id] = {membership.user_id: membership for membership in memberships}
    return cache[chat_room.id]


def member_summary(serializer, chat_room, user_id) -> dict | None:
    """방 안에서 보여줄 유저 정보"""
    if user_id is None:
        return None

    membership = member_directory(serializer, chat_room).get(user_id)
    request = serializer.context.get("request")
    return {
        "display_name": membership.get_display_name() if membership else "(알 수 없음)",
        "anon_number": membership.anon_number if membership else None,
        "role": membership.role if membership else None,
        "is_mine": bool(request and request.user.id == user_id),
    }


def is_anonymous_room(chat_room) -> bool:
    return chat_room.chat_name_type == ChatNameType.ANONYMOUS.value
