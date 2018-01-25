from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Scrap
from apps.core.serializers.scrap import ScrapSerializer, ScrapCreateActionSerializer


class ScrapViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, ActionAPIViewSet):
    queryset = Scrap.objects.all()
    serializer_class = ScrapSerializer
    action_serializer_class = {
        'create': ScrapCreateActionSerializer,
    }

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )
