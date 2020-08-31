from rest_framework import mixins, decorators, status, response

from apps.core.permissions.block import BlockPermission
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Block
from apps.core.serializers.block import (
    BlockSerializer,
    BlockCreateActionSerializer,
    BlockDestroyWithoutIdSerializer)


class BlockViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   ActionAPIViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    action_serializer_class = {
        'create': BlockCreateActionSerializer,
        'without_id': BlockDestroyWithoutIdSerializer,
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

    @decorators.action(detail=False, methods=['post'])
    def without_id(self, request, *args, **kwargs):
        print('request', request)
        instance = Block.objects.get(blocked_by=request.user, user=request.data.get('blocked'))
        self.perform_destroy(instance)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
