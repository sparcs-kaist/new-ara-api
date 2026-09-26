from django.db.models import Prefetch, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, permissions, response, status
from rest_framework.decorators import action

from ara.classes.viewset import ActionAPIViewSet
from apps.meal.models import Store, StoreEvent, StoreMenu, StoreNotice, StoreStaff
from apps.meal.serializers.store_serializers import (
    StoreDetailSerializer,
    StoreEventSerializer,
    StoreListSerializer,
    StoreMenuSerializer,
    StoreNoticeSerializer,
    StoreUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(parameters=[
        OpenApiParameter("zone", OpenApiTypes.STR, enum=["EAST", "WEST", "NORTH"]),
        OpenApiParameter("q", OpenApiTypes.STR, description="업체 이름 / 분류 / 메뉴 이름"),
    ]),
)
class StoreViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, ActionAPIViewSet):
    serializer_class = StoreDetailSerializer
    pagination_class = None

    action_permission_classes = {
        "list": (permissions.AllowAny,),
        "retrieve": (permissions.AllowAny,),
        "partial_update": (permissions.IsAuthenticated,),
        "menus": (permissions.IsAuthenticated,),
        "menu_detail": (permissions.IsAuthenticated,),
        "notices": (permissions.IsAuthenticated,),
        "notice_detail": (permissions.IsAuthenticated,),
        "events": (permissions.IsAuthenticated,),
        "event_detail": (permissions.IsAuthenticated,),
        "mine": (permissions.IsAuthenticated,),
    }
    action_serializer_class = {
        "list": StoreListSerializer,
        "partial_update": StoreUpdateSerializer,
        "menus": StoreMenuSerializer,
        "menu_detail": StoreMenuSerializer,
        "notices": StoreNoticeSerializer,
        "notice_detail": StoreNoticeSerializer,
        "events": StoreEventSerializer,
        "event_detail": StoreEventSerializer,
    }

    def get_queryset(self):
        # 끝나지 않은 이벤트 (시작 전 포함). 영업 상태 계산과 events 목록에 같이 쓴다
        current_events = StoreEvent.objects.filter(Q(ends_at__isnull=True) | Q(ends_at__gte=timezone.now()))
        queryset = Store.objects.filter(is_active=True).prefetch_related(
            Prefetch("events", queryset=current_events, to_attr="current_events"),
            Prefetch("menus", queryset=StoreMenu.objects.filter(is_signature=True), to_attr="signature_list"),
        )
        if self.action == "list":
            zone = self.request.query_params.get("zone")
            if zone:
                queryset = queryset.filter(zone=zone)
            q = self.request.query_params.get("q", "").strip()
            if q:
                menu_store_ids = StoreMenu.objects.filter(name__icontains=q).values("store_id")
                queryset = queryset.filter(Q(name__icontains=q) | Q(category__icontains=q) | Q(id__in=menu_store_ids))
            return queryset
        return queryset.prefetch_related(Prefetch("menus", queryset=StoreMenu.objects.order_by("order", "id")))

    def get_staff_store(self):
        store = self.get_object()
        if not store.is_staff(self.request.user):
            raise exceptions.PermissionDenied("이 업체를 관리하는 계정이 아니에요.")
        return store

    def save_child(self, request, serializer_class, instance=None, **extra):
        serializer = serializer_class(instance, data=request.data, partial=instance is not None)
        serializer.is_valid(raise_exception=True)
        return serializer.save(**extra)

    # 직원: 운영 여부 / 식당 연결 / 정렬 외 업체 정보 전부
    def partial_update(self, request, pk=None):
        store = self.get_staff_store()
        self.save_child(request, StoreUpdateSerializer, store)
        store = self.get_queryset().get(pk=store.pk)
        return response.Response(StoreDetailSerializer(store, context=self.get_serializer_context()).data)

    @extend_schema(request=StoreMenuSerializer, responses={201: StoreMenuSerializer})
    @action(detail=True, methods=["post"])
    def menus(self, request, pk=None):
        store = self.get_staff_store()
        menu = self.save_child(request, StoreMenuSerializer, store=store)
        return response.Response(StoreMenuSerializer(menu).data, status=status.HTTP_201_CREATED)

    # PATCH : 메뉴 수정 (품절 포함) / DELETE : 메뉴 삭제
    @extend_schema(request=StoreMenuSerializer, responses={200: StoreMenuSerializer, 204: None})
    @action(detail=True, methods=["patch", "delete"], url_path=r"menus/(?P<menu_id>\d+)")
    def menu_detail(self, request, pk=None, menu_id=None):
        store = self.get_staff_store()
        menu = store.menus.filter(pk=menu_id).first()
        if menu is None:
            raise exceptions.NotFound("메뉴를 찾을 수 없어요.")
        if request.method == "DELETE":
            menu.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(StoreMenuSerializer(self.save_child(request, StoreMenuSerializer, menu)).data)

    @extend_schema(request=StoreNoticeSerializer, responses={201: StoreNoticeSerializer})
    @action(detail=True, methods=["post"])
    def notices(self, request, pk=None):
        store = self.get_staff_store()
        notice = self.save_child(request, StoreNoticeSerializer, store=store)
        return response.Response(StoreNoticeSerializer(notice).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=StoreNoticeSerializer, responses={200: StoreNoticeSerializer, 204: None})
    @action(detail=True, methods=["patch", "delete"], url_path=r"notices/(?P<notice_id>\d+)")
    def notice_detail(self, request, pk=None, notice_id=None):
        store = self.get_staff_store()
        notice = store.notices.filter(pk=notice_id).first()
        if notice is None:
            raise exceptions.NotFound("공지를 찾을 수 없어요.")
        if request.method == "DELETE":
            notice.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(StoreNoticeSerializer(self.save_child(request, StoreNoticeSerializer, notice)).data)

    @extend_schema(request=StoreEventSerializer, responses={200: StoreEventSerializer(many=True), 201: StoreEventSerializer})
    @action(detail=True, methods=["get", "post"])
    def events(self, request, pk=None):
        store = self.get_staff_store()
        if request.method == "GET":
            return response.Response(StoreEventSerializer(store.current_events, many=True).data)
        event = self.save_child(request, StoreEventSerializer, store=store)
        return response.Response(StoreEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=StoreEventSerializer, responses={200: StoreEventSerializer, 204: None})
    @action(detail=True, methods=["patch", "delete"], url_path=r"events/(?P<event_id>\d+)")
    def event_detail(self, request, pk=None, event_id=None):
        store = self.get_staff_store()
        event = store.events.filter(pk=event_id).first()
        if event is None:
            raise exceptions.NotFound("이벤트를 찾을 수 없어요.")
        if request.method == "DELETE":
            event.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        return response.Response(StoreEventSerializer(self.save_child(request, StoreEventSerializer, event)).data)

    # 내가 관리하는 업체 id 목록
    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    @action(detail=False, methods=["get"])
    def mine(self, request):
        store_ids = StoreStaff.objects.filter(user=request.user).values_list("store_id", flat=True)
        return response.Response({"store_ids": list(store_ids)})
