from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import BlackList
from apps.core.serializers.black_list import BlackListSerializer, BlackListCreateActionSerializer


class BlackListViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = BlackList.objects.all()
    serializer_class = BlackListSerializer
    action_serializer_class = {
        'create': BlackListCreateActionSerializer,
    }

    def perform_create(self, serializer):
        serializer.save(
            black_from=self.request.user,
        )
