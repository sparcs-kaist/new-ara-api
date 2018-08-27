from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Scrap
from apps.core.permissions.scrap import ScrapPermission
from apps.core.serializers.scrap import ScrapSerializer, ScrapCreateActionSerializer


class ScrapViewSet(mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.DestroyModelMixin,
                   ActionAPIViewSet):
    queryset = Scrap.objects.all()
    serializer_class = ScrapSerializer
    action_serializer_class = {
        'create': ScrapCreateActionSerializer,
    }
    permission_classes = (
        ScrapPermission,
    )

    def get_queryset(self):
        queryset = super(ScrapViewSet, self).get_queryset()

        queryset = queryset.filter(
            scrapped_by=self.request.user,
        ).prefetch_related(
            'parent_article',
            'parent_article__attachments',
            'scrapped_by',
            'scrapped_by__profile',
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )
