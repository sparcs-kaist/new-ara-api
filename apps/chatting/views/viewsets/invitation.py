from rest_framework import (
    decorators,
    permissions,
    response,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action

from drf_spectacular.utils import extend_schema, extend_schema_view

from datetime import timezone

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models.room import ChatRoom
from apps.chatting.models.room_invitation import ChatRoomInvitation
from apps.chatting.permissions.invitation import (
    CreateInvitationPermission,
    DeleteInvitationPermission,
    AcceptInvitationPermission,
    RejectInvitationPermission,
)
from apps.chatting.serializers.invitation import (
    ChatInvitationSerializer,
    ChatInvitationCreateSerializer,
)


@extend_schema_view(
    update=extend_schema(exclude=True),
    partial_update=extend_schema(exclude=True),
)
class ChatInvitationViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = ChatRoomInvitation.objects.all()
    serializer_class = ChatInvitationSerializer

    action_permission_classes = {
        "accept": (permissions.IsAuthenticated, AcceptInvitationPermission,),
        "deny": (permissions.IsAuthenticated, RejectInvitationPermission,),
        "create": (CreateInvitationPermission,),
        "list": (permissions.IsAuthenticated,),
        "destroy": (DeleteInvitationPermission,),
        "retrieve": (permissions.IsAuthenticated,),
    }

    action_serializer_class = {
        "create": ChatInvitationCreateSerializer,
    }
    
    def get_queryset(self):
        # list 액션일 경우 자신이 받은 초대장만 조회
        if self.action == "list":
            return ChatRoomInvitation.objects.filter(invitation_to=self.request.user)
        return super().get_queryset()
    
    # 초대장 수락 (POST /chat/invitations/{id}/accept/)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        invitation = self.get_object()
        try:
            invitation.accept_invitation()
            return response.Response(status=status.HTTP_200_OK)
        except Exception as e:
            return response.Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # 초대장 거절 (POST /chat/invitations/{id}/deny/)
    @action(detail=True, methods=["post"])
    def deny(self, request, pk=None):
        invitation = self.get_object()
        invitation.reject_invitation()
        return response.Response(status=status.HTTP_200_OK)