from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Block
from apps.core.serializers.block import BlockSerializer, BlockCreateActionSerializer


class BlockViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    action_serializer_class = {
        'create': BlockCreateActionSerializer,
    }

    def perform_create(self, serializer):
        serializer.save(
            blocked_by=self.request.user,
        )
