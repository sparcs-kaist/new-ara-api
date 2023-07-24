from rest_framework import permissions, viewsets

from apps.core.models import BoardGroup
from apps.core.serializers.board_group import BoardGroupSerializer


class BoardGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BoardGroup.objects.all()
    serializer_class = BoardGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"
    pagination_class = None
