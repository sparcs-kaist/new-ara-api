from rest_framework import permissions, viewsets

from apps.core.models import Board
from apps.core.serializers.board import BoardDetailActionSerializer, BoardSerializer
from ara.classes.viewset import ActionAPIViewSet


class BoardViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    pagination_class = None
    queryset = Board.objects.all().reverse()
    filterset_fields = ["is_readonly", "is_hidden"]
    serializer_class = BoardSerializer
    permission_classes = (permissions.IsAuthenticated,)
    action_serializer_class = {
        "list": BoardDetailActionSerializer,
    }
