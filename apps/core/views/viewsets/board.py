from rest_framework import viewsets, permissions

from apps.core.filters.board import BoardFilter
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Board
from apps.core.serializers.board import (
    BoardSerializer,
    BoardDetailActionSerializer,
)


class BoardViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = Board.objects.all()
    filterset_class = BoardFilter
    serializer_class = BoardSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
    action_serializer_class = {
        'retrieve': BoardDetailActionSerializer,
    }
