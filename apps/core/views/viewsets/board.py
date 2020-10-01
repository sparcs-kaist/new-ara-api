from rest_framework import viewsets, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Board
from apps.core.serializers.board import (
    BoardSerializer,
    BoardDetailActionSerializer,
)


class BoardViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = Board.objects.all().reverse()
    filterset_fields = ['is_readonly', 'is_hidden']
    serializer_class = BoardSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
    action_serializer_class = {
        'list': BoardDetailActionSerializer,
    }
