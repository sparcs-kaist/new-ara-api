from rest_framework import viewsets, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Board
from apps.core.serializers.board import BoardSerializer


class BoardViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
