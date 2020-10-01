from rest_framework import viewsets, permissions

from ara.classes.viewset import ActionAPIViewSet
from apps.core.serializers.best_search import BestSearchSerializer
from apps.core.models import BestSearch


class BestSearchViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = BestSearch.objects.all()
    filterset_fields = ['latest']
    serializer_class = BestSearchSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
