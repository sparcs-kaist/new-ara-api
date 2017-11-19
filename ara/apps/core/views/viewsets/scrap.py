from datetime import datetime

from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Scrap
#from apps.core.filters.article import ArticleFilter
#from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.scrap import ScrapSerializer, \
        ScrapCreateActionSerializer

class ScrapViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Scrap.objects.all()
    #filter_class = ArticleFilter
    serializer_class = ScrapSerializer
    action_serializer_class = {
        'create': ScrapCreateActionSerializer,
    }
    #permission_classes = (
    #    ArticlePermission,
    #)

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )





