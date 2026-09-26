from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import exceptions, mixins, permissions, response, serializers, status, viewsets
from rest_framework.decorators import action

from apps.meal.models import Restaurant, Store, StoreStaff
from apps.meal.serializers.store_serializers import validate_hours_value
from apps.user.models import UserProfile

User = get_user_model()


class OpsStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            "id", "name", "intro", "zone", "location", "hours", "hours_note", "cover", "phone", "link",
            "restaurant", "is_active", "order",
        ]

    def validate_hours(self, value):
        return validate_hours_value(value)


class OpsRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "restaurant_name", "code", "display_name", "is_active"]
        read_only_fields = ["restaurant_name"]


def user_summary(user) -> dict:
    profile = getattr(user, "profile", None)
    return {
        "id": user.id,
        "nickname": profile.nickname if profile else None,
        "email": user.email,
        "group": profile.group if profile else None,
    }


# 운영진(is_staff) 전용. 식사 탭 관리 웹 페이지가 쓴다
class OpsStoreViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Store.objects.all()
    serializer_class = OpsStoreSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None

    @action(detail=True, methods=["get", "post"])
    def staff(self, request, pk=None):
        store = self.get_object()
        if request.method == "GET":
            staff = store.staff.select_related("user__profile")
            return response.Response([user_summary(s.user) for s in staff])

        user = User.objects.filter(pk=request.data.get("user_id")).select_related("profile").first()
        if user is None:
            raise exceptions.ValidationError({"detail": "없는 계정이에요."})
        # 입주업체 직원 그룹은 대부분 게시판에 글을 못 쓰므로, 그룹 변경은 운영진이 확인했을 때만 한다
        profile = getattr(user, "profile", None)
        if not profile or profile.group != UserProfile.UserGroup.STORE_EMPLOYEE:
            if not request.data.get("grant_group"):
                raise exceptions.ValidationError({
                    "detail": "입주업체 직원(STORE_EMPLOYEE) 그룹이 아닌 계정이에요. 그룹을 바꾸면 대부분 게시판에 글을 쓸 수 없게 돼요.",
                    "code": "group_required",
                })
            if profile is None:
                raise exceptions.ValidationError({"detail": "프로필이 없는 계정이에요."})
            profile.group = UserProfile.UserGroup.STORE_EMPLOYEE
            profile.save(update_fields=["group"])

        StoreStaff.objects.get_or_create(store=store, user=user)
        return response.Response(user_summary(user), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"staff/(?P<user_id>\d+)")
    def staff_detail(self, request, pk=None, user_id=None):
        self.get_object().staff.filter(user_id=user_id).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


class OpsRestaurantViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Restaurant.objects.order_by("id")
    serializer_class = OpsRestaurantSerializer
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None


# 직원 지정용 계정 검색 (닉네임 / 이메일)
class OpsUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAdminUser,)
    pagination_class = None

    def list(self, request):
        q = request.query_params.get("q", "").strip()
        if len(q) < 2:
            return response.Response([])
        users = User.objects.filter(
            Q(profile__nickname__icontains=q) | Q(email__icontains=q),
        ).select_related("profile")[:20]
        return response.Response([user_summary(user) for user in users])
