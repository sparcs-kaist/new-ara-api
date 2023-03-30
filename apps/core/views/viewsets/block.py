from dateutil.relativedelta import relativedelta
from django.utils import timezone
from rest_framework import decorators, mixins, response, status

from apps.core.models import Block
from apps.core.permissions.block import BlockPermission
from apps.core.serializers.block import (
    BlockCreateActionSerializer,
    BlockDestroyWithoutIdSerializer,
    BlockSerializer,
)
from ara.classes.viewset import ActionAPIViewSet


class BlockViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    action_serializer_class = {
        "create": BlockCreateActionSerializer,
        "without_id": BlockDestroyWithoutIdSerializer,
    }
    permission_classes = (BlockPermission,)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # cacheops 이용으로 select_related에서 prefetch_related로 옮김
        queryset = (
            queryset.filter(
                blocked_by=self.request.user,
            )
            .select_related()
            .prefetch_related(
                "user",
                "user__profile",
            )
        )

        return queryset

    def create(self, request, *args, **kwargs):
        # 하루 block 제한 10개
        recent_block_count = (
            Block.objects.queryset_with_deleted.filter(
                created_at__gt=(timezone.now() - relativedelta(days=1))
            )
            .filter(blocked_by=self.request.user)
            .count()
        )
        if recent_block_count >= 10:
            return response.Response(
                {"message": "더 이상 사용자를 차단할 수 없습니다. 24시간 내에 최대 10번 차단할 수 있습니다"},
                status=status.HTTP_403_FORBIDDEN,
            )
        else:
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            blocked_by=self.request.user,
        )

    @decorators.action(detail=False, methods=["post"])
    def without_id(self, request, *args, **kwargs):
        instance = Block.objects.get(
            blocked_by=request.user, user=request.data.get("blocked")
        )
        self.perform_destroy(instance)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
