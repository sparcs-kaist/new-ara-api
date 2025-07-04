from rest_framework import routers
from apps.chatting.views import viewsets

router = routers.DefaultRouter()

# 채팅방 관련 ViewSet
router.register(
    prefix=r"chat/room",
    viewset=viewsets.ChatRoomViewSet,
    basename="chat_room"
)

"""
# 메시지 관련 ViewSet
router.register(
    prefix=r"chat/message",
    viewset=viewsets.ChatMessageViewSet,
    basename="chat_message"
)
아직 구현이 안 된 부분.
"""

# 채팅방 초대 관련 ViewSet
router.register(
    prefix=r"chat/invitation",
    viewset=viewsets.ChatInvitationViewSet,
    basename="chat_invitation"
)

# DM 관련 ViewSet
router.register(
    prefix=r"chat/dm",
    viewset=viewsets.DMViewSet,
    basename="chat_dm"
)

