from rest_framework import mixins

from apps.core.permissions.block import BlockPermission
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Block
from apps.core.serializers.block import (
    BlockSerializer,
    BlockCreateActionSerializer,
)


class BlockViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   ActionAPIViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    action_serializer_class = {
        'create': BlockCreateActionSerializer,
    }
    permission_classes = (BlockPermission,)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # cacheops 이용으로 select_related에서 prefetch_related로 옮김
        queryset = queryset.filter(
            blocked_by=self.request.user,
        ).select_related(
        ).prefetch_related(
            'user',
            'user__profile',
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            blocked_by=self.request.user,
        )
