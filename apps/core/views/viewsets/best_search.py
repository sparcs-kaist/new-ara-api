from rest_framework import permissions, viewsets

from apps.core.models import BestSearch
from apps.core.serializers.best_search import BestSearchSerializer
from ara.classes.viewset import ActionAPIViewSet


class BestSearchViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = BestSearch.objects.all()
    filterset_fields = ["latest"]
    serializer_class = BestSearchSerializer
    permission_classes = (permissions.IsAuthenticated,)
