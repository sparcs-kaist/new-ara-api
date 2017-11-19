from datetime import datetime

from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import BlackList
#from apps.core.filters.article import ArticleFilter
#from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.black_list import BlackListSerializer, BlackListCreateActionSerializer

class BlackListViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = BlackList.objects.all()
    #filter_class = ArticleFilter
    serializer_class = BlackListSerializer
    action_serializer_class = {
        'create': BlackListCreateActionSerializer,
    }
    #permission_classes = (
    #    ArticlePermission,
    #)

    def perform_create(self, serializer):
        serializer.save(
            black_from=self.request.user,
        )





