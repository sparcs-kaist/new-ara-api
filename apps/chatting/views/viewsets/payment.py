from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, mixins, permissions, response, status
from rest_framework.decorators import action
from django.db import transaction

from ara.classes.viewset import ActionAPIViewSet
from ara.settings import MIN_TIME
from apps.chatting.models.membership_room import ChatRoomMemberShip
from apps.chatting.models.payment import ChatPaymentRequest
from apps.chatting.models.room import ChatRoomType
from apps.chatting.realtime import broadcast_message_created, broadcast_room_update
from apps.chatting.serializers.payment import (
    ChatPaymentPaidSerializer,
    ChatPaymentRequestCreateSerializer,
    ChatPaymentRequestSerializer,
    ChatPaymentRequestUpdateSerializer,
)
from apps.chatting.views.viewsets.vote import get_membership_or_403


class ChatPaymentViewSet(mixins.RetrieveModelMixin, ActionAPIViewSet):
    queryset = ChatPaymentRequest.objects.filter(
        message__deleted_at=MIN_TIME,
    ).select_related("message__chat_room").prefetch_related("targets")
    serializer_class = ChatPaymentRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    action_serializer_class = {
        "create": ChatPaymentRequestCreateSerializer,
        "paid": ChatPaymentPaidSerializer,
        "partial_update": ChatPaymentRequestUpdateSerializer,
    }

    def get_object(self):
        payment_request = super().get_object()
        get_membership_or_403(payment_request.message.chat_room, self.request.user)
        return payment_request

    def payment_response(self, payment_request, status_code=status.HTTP_200_OK):
        payment_request = self.get_queryset().get(pk=payment_request.pk)
        return response.Response(
            ChatPaymentRequestSerializer(payment_request, context=self.get_serializer_context()).data,
            status=status_code,
        )

    @extend_schema(responses={201: ChatPaymentRequestSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        chat_room = data["chat_room"]
        get_membership_or_403(chat_room, request.user)

        if chat_room.room_type == ChatRoomType.DELIVERY.value:
            raise exceptions.ValidationError("함께 배달 방은 배달 정산 API 를 사용해주세요.")

        targets = [(target["user"], target["amount"]) for target in data["targets"]]
        for user, _ in targets:
            if user == request.user:
                raise exceptions.ValidationError("자기 자신에게는 정산을 요청할 수 없습니다.")
            if ChatRoomMemberShip.get_active(chat_room, user) is None:
                raise exceptions.ValidationError("채팅방 참여자에게만 정산을 요청할 수 있습니다.")

        payment_request = ChatPaymentRequest.create_with_message(
            chat_room=chat_room,
            created_by=request.user,
            bank_name=data["bank_name"],
            account_number=data["account_number"],
            targets=targets,
        )
        broadcast_message_created(payment_request.message)
        return self.payment_response(payment_request, status.HTTP_201_CREATED)

    # (요청자) 은행 / 계좌번호 수정. 아무도 송금하기 전에만
    @extend_schema(request=ChatPaymentRequestUpdateSerializer, responses={200: ChatPaymentRequestSerializer})
    @transaction.atomic
    def partial_update(self, request, pk=None):
        payment_request = self.get_object()
        if payment_request.message.created_by_id != request.user.id:
            raise exceptions.PermissionDenied("정산을 요청한 사람만 고칠 수 있습니다.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_request.lock_row()
        if payment_request.has_paid_target():
            raise exceptions.ValidationError({"detail": "이미 송금한 사람이 있어 고칠 수 없습니다."})
        for name, value in serializer.validated_data.items():
            setattr(payment_request, name, value)
        payment_request.save()

        broadcast_room_update(payment_request.message.chat_room_id, "payment", "updated", payment_request.id)
        return self.payment_response(payment_request)

    @extend_schema(request=ChatPaymentPaidSerializer, responses={200: ChatPaymentRequestSerializer})
    @action(detail=True, methods=["patch"])
    @transaction.atomic
    def paid(self, request, pk=None):
        payment_request = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment_request.lock_row()
        target = payment_request.targets.filter(user=request.user).first()
        if target is None:
            raise exceptions.PermissionDenied("정산 대상자가 아닙니다.")
        target.set_paid(serializer.validated_data["paid"])

        broadcast_room_update(payment_request.message.chat_room_id, "payment", "updated", payment_request.id)
        return self.payment_response(payment_request)
