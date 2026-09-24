from django.db.models import Count, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, permissions, response, status
from rest_framework.decorators import action

from ara.classes.viewset import ActionAPIViewSet
from apps.chatting.models import ChatRoomMemberShip
from apps.chatting.serializers.payment import ChatPaymentRequestSerializer
from apps.delivery.models import (
    DeliveryActionError,
    DeliveryOrder,
    DeliveryParty,
    DeliveryStatus,
)
from apps.delivery.serializers.delivery import (
    DeliveryExtendSerializer,
    DeliveryOrderCreateSerializer,
    DeliveryOrderSerializer,
    DeliveryPartyCreateSerializer,
    DeliveryPartyDetailSerializer,
    DeliveryPartyListSerializer,
    DeliveryPaymentRequestSerializer,
)


class DeliveryRuleViolation(exceptions.APIException):
    # ValidationError 는 {"detail": ["..."]} 로 감싸므로 문자열 그대로 내려주려고 따로 둔다
    status_code = 400
    default_code = "delivery_rule"


def run_action(fn, *args, **kwargs):
    """DeliveryActionError -> 400 / 403 ({"detail": "문구"})"""
    try:
        return fn(*args, **kwargs)
    except DeliveryActionError as e:
        if e.forbidden:
            raise exceptions.PermissionDenied(e.message)
        raise DeliveryRuleViolation(e.message)


@extend_schema_view(
    list=extend_schema(
        description="함께 배달 방 목록. 기본은 모집 중인 방을 마감 임박 순으로",
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="식당 또는 배달 장소 검색"),
            OpenApiParameter("joined", OpenApiTypes.BOOL, description="true 면 내가 참여한 방 (상태 무관, 최신순)"),
        ],
    ),
)
class DeliveryPartyViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, ActionAPIViewSet):
    """
    GET    /api/delivery/                          목록
    POST   /api/delivery/                          방 만들기 (방장 주문 포함)
    GET    /api/delivery/<id>/                     상세
    POST   /api/delivery/<id>/join/                참여
    POST   /api/delivery/<id>/leave/               나가기
    POST   /api/delivery/<id>/orders/              주문 넣기
    DELETE /api/delivery/<id>/orders/<order_id>/   주문 취소
    POST   /api/delivery/<id>/confirm/             (방장) 주문 확정
    POST   /api/delivery/<id>/extend/              (방장) 모집 연장
    POST   /api/delivery/<id>/cancel/              (방장) 모집 취소
    POST   /api/delivery/<id>/arrive/              (방장) 배달 도착 알림
    POST   /api/delivery/<id>/payment-request/     (방장) 정산 요청 (금액 자동 계산)
    """
    serializer_class = DeliveryPartyDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)

    action_serializer_class = {
        "list": DeliveryPartyListSerializer,
        "create": DeliveryPartyCreateSerializer,
        "orders": DeliveryOrderCreateSerializer,
        "extend": DeliveryExtendSerializer,
        "payment_request": DeliveryPaymentRequestSerializer,
    }

    def get_queryset(self):
        total_amount = DeliveryOrder.objects.filter(
            party=OuterRef("pk"), canceled_at__isnull=True,
        ).values("party").annotate(total=Sum("price")).values("total")
        participant_count = ChatRoomMemberShip.objects.filter(
            chat_room=OuterRef("chat_room"),
        ).values("chat_room").annotate(count=Count("id")).values("count")

        queryset = DeliveryParty.objects.annotate(
            total_amount=Coalesce(Subquery(total_amount), 0),
            participant_count=Coalesce(Subquery(participant_count), 0),
        )

        if self.action != "list":
            return queryset

        params = self.request.query_params
        if params.get("joined") == "true":
            my_room_ids = ChatRoomMemberShip.objects.filter(
                user=self.request.user,
            ).values("chat_room_id")
            queryset = queryset.filter(chat_room_id__in=my_room_ids).order_by("-created_at")
        else:
            queryset = queryset.filter(
                status=DeliveryStatus.RECRUITING.value,
                deadline_at__gt=timezone.now(),
            ).order_by("deadline_at")

        search = params.get("search")
        if search:
            queryset = queryset.filter(Q(store_name__icontains=search) | Q(place_name__icontains=search))
        return queryset

    def detail_response(self, party, status_code=status.HTTP_200_OK):
        party = self.get_queryset().get(pk=party.pk)
        return response.Response(
            DeliveryPartyDetailSerializer(party, context=self.get_serializer_context()).data,
            status=status_code,
        )

    def validated_input(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    @extend_schema(responses={201: DeliveryPartyDetailSerializer})
    def create(self, request):
        party = run_action(DeliveryParty.open, request.user, **self.validated_input(request))
        return self.detail_response(party, status.HTTP_201_CREATED)

    @extend_schema(request=None, responses={200: DeliveryPartyDetailSerializer})
    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        party = self.get_object()
        run_action(party.join, request.user)
        return self.detail_response(party)

    @extend_schema(request=None, responses={204: None})
    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        party = self.get_object()
        run_action(party.leave, request.user)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=DeliveryOrderCreateSerializer, responses={201: DeliveryOrderSerializer})
    @action(detail=True, methods=["post"])
    def orders(self, request, pk=None):
        party = self.get_object()
        order = run_action(party.place_order, request.user, **self.validated_input(request))
        return response.Response(
            DeliveryOrderSerializer(order, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=None, responses={204: None})
    @action(detail=True, methods=["delete"], url_path=r"orders/(?P<order_id>\d+)")
    def cancel_order(self, request, pk=None, order_id=None):
        party = self.get_object()
        order = DeliveryOrder.objects.filter(pk=order_id, party=party).first()
        if order is None:
            raise exceptions.NotFound("주문을 찾을 수 없어요.")
        run_action(party.cancel_order, order, request.user)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None, responses={200: DeliveryPartyDetailSerializer})
    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        party = self.get_object()
        run_action(party.confirm_order, request.user)
        return self.detail_response(party)

    @extend_schema(request=DeliveryExtendSerializer, responses={200: DeliveryPartyDetailSerializer})
    @action(detail=True, methods=["post"])
    def extend(self, request, pk=None):
        party = self.get_object()
        run_action(party.extend, request.user, self.validated_input(request)["minutes"])
        return self.detail_response(party)

    @extend_schema(request=None, responses={200: DeliveryPartyDetailSerializer})
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        party = self.get_object()
        run_action(party.cancel, request.user)
        return self.detail_response(party)

    @extend_schema(request=None, responses={200: DeliveryPartyDetailSerializer})
    @action(detail=True, methods=["post"])
    def arrive(self, request, pk=None):
        party = self.get_object()
        run_action(party.arrive, request.user)
        return self.detail_response(party)

    @extend_schema(request=DeliveryPaymentRequestSerializer, responses={201: ChatPaymentRequestSerializer})
    @action(detail=True, methods=["post"], url_path="payment-request")
    def payment_request(self, request, pk=None):
        party = self.get_object()
        payment_request = run_action(party.request_payment, request.user, **self.validated_input(request))
        return response.Response(
            ChatPaymentRequestSerializer(payment_request, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )
