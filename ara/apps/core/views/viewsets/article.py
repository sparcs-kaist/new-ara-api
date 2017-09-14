from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Article
from apps.core.filters.article import ArticleFilter
from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.article import ArticleSerializer, \
    ArticleCreateActionSerializer, ArticleUpdateActionSerializer


class ArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Article.objects.all()
    filter_class = ArticleFilter
    serializer_class = ArticleSerializer
    action_serializer_class = {
        'create': ArticleCreateActionSerializer,
        'update': ArticleUpdateActionSerializer,
        'partial_update': ArticleUpdateActionSerializer,
    }
    permission_classes = (
        ArticlePermission,
    )

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )
