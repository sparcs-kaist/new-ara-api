from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, mixins, permissions, response, status
from rest_framework.decorators import action

from ara.classes.viewset import ActionAPIViewSet
from ara.settings import MIN_TIME
from apps.chatting.models.membership_room import ChatRoomMemberShip
from apps.chatting.models.vote import ChatVote
from apps.chatting.realtime import broadcast_message_created, broadcast_room_update
from apps.chatting.serializers.vote import (
    ChatVoteCastSerializer,
    ChatVoteCreateSerializer,
    ChatVoteSerializer,
)


def get_membership_or_403(chat_room, user):
    membership = ChatRoomMemberShip.get_active(chat_room, user)
    if membership is None:
        raise exceptions.PermissionDenied("채팅방 참여자가 아닙니다.")
    return membership


class ChatVoteViewSet(mixins.RetrieveModelMixin, ActionAPIViewSet):
    queryset = ChatVote.objects.filter(
        message__deleted_at=MIN_TIME,
    ).select_related("message__chat_room").prefetch_related("options__ballots")
    serializer_class = ChatVoteSerializer
    permission_classes = (permissions.IsAuthenticated,)

    action_serializer_class = {
        "create": ChatVoteCreateSerializer,
        "ballot": ChatVoteCastSerializer,
    }

    def get_object(self):
        vote = super().get_object()
        get_membership_or_403(vote.message.chat_room, self.request.user)
        return vote

    @extend_schema(responses={201: ChatVoteSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        get_membership_or_403(data["chat_room"], request.user)

        vote = ChatVote.create_with_message(
            chat_room=data["chat_room"],
            created_by=request.user,
            title=data["title"],
            options=data["options"],
            max_choices=data["max_choices"],
        )
        broadcast_message_created(vote.message)

        vote = self.get_queryset().get(pk=vote.pk)
        return response.Response(
            ChatVoteSerializer(vote, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=ChatVoteCastSerializer, responses={200: ChatVoteSerializer})
    @action(detail=True, methods=["put"])
    def ballot(self, request, pk=None):
        vote = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            vote.cast(request.user, serializer.validated_data["option_ids"])
        except DjangoValidationError as e:
            raise exceptions.ValidationError(e.messages)

        broadcast_room_update(vote.message.chat_room_id, "vote", "updated", vote.id)

        vote = self.get_queryset().get(pk=vote.pk)
        return response.Response(ChatVoteSerializer(vote, context=self.get_serializer_context()).data)
