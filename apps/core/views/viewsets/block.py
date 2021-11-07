from rest_framework import mixins, decorators, status, response

from apps.core.permissions.block import BlockPermission
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Block, block
from apps.core.serializers.block import (
    BlockSerializer,
    BlockCreateActionSerializer,
    BlockDestroyWithoutIdSerializer)

from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.utils.translation import gettext

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

    def create(self, request, *args, **kwargs):
        # 하루 block 제한 10개
        block_num = Block.objects.queryset_with_deleted.filter(created_at__gte=(timezone.now() - relativedelta(days=1))).filter(blocked_by=self.request.user).count()
        if(block_num >= 10):
            return response.Response({'message': gettext('Cannot block anymore. 10 block allowed for 24 hours')},status=status.HTTP_403_FORBIDDEN)
        else:
            return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            blocked_by=self.request.user,
        )

    @decorators.action(detail=False, methods=['post'])
    def without_id(self, request, *args, **kwargs):
        instance = Block.objects.get(blocked_by=request.user, user=request.data.get('blocked'))
        self.perform_destroy(instance)
        return response.Response(status=status.HTTP_204_NO_CONTENT)
