from datetime import date as date_type

from django.db.models import Case, IntegerField, Value, When
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, permissions, response, status

from ara.classes.viewset import ActionAPIViewSet
from apps.meal.models import MAX_PHOTOS_PER_MEAL, MenuPhoto
from apps.meal.serializers.menu_photo_serializers import MenuPhotoCreateSerializer, MenuPhotoSerializer
from apps.user.models import UserProfile


@extend_schema_view(
    list=extend_schema(
        description="끼니별 메뉴 사진. 공식(입주업체) 사진이 먼저, 그다음 최신순",
        parameters=[
            OpenApiParameter("restaurant_id", OpenApiTypes.INT, required=True),
            OpenApiParameter("date", OpenApiTypes.STR, required=True, description="YYYYMMDD"),
            OpenApiParameter("meal_time", OpenApiTypes.STR, required=False, enum=["BREAKFAST", "LUNCH", "DINNER"]),
        ],
    ),
)
class MenuPhotoViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, ActionAPIViewSet):
    serializer_class = MenuPhotoSerializer

    action_permission_classes = {
        "list": (permissions.AllowAny,),
        "create": (permissions.IsAuthenticated,),
        "destroy": (permissions.IsAuthenticated,),
    }
    action_serializer_class = {
        "create": MenuPhotoCreateSerializer,
    }

    def get_queryset(self):
        queryset = MenuPhoto.objects.select_related("restaurant", "created_by__profile")
        if self.action != "list":
            return queryset

        params = self.request.query_params
        try:
            date_str = params["date"]
            query_date = date_type(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
            queryset = queryset.filter(restaurant_id=int(params["restaurant_id"]), date=query_date)
        except (KeyError, ValueError, TypeError):
            raise exceptions.ValidationError({"detail": "restaurant_id 와 date(YYYYMMDD)가 필요합니다."})
        if params.get("meal_time"):
            queryset = queryset.filter(meal_time=params["meal_time"])

        return queryset.annotate(
            official_first=Case(
                When(created_by__profile__group=UserProfile.UserGroup.STORE_EMPLOYEE, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        ).order_by("official_first", "-created_at")

    @extend_schema(request=MenuPhotoCreateSerializer, responses={201: MenuPhotoSerializer})
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        uploaded = MenuPhoto.objects.filter(
            created_by=request.user,
            restaurant=data["restaurant"],
            date=data["date"],
            meal_time=data["meal_time"],
        ).count()
        if uploaded >= MAX_PHOTOS_PER_MEAL:
            raise exceptions.ValidationError({"detail": f"한 끼니에 사진은 {MAX_PHOTOS_PER_MEAL}장까지 올릴 수 있어요."})

        photo = MenuPhoto.objects.create(created_by=request.user, **data)
        return response.Response(
            MenuPhotoSerializer(photo, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    # 관리자는 admin 에서 지운다
    def perform_destroy(self, instance):
        if instance.created_by_id != self.request.user.id:
            raise exceptions.PermissionDenied("내가 올린 사진만 지울 수 있어요.")
        instance.delete()
