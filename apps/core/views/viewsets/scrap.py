from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import (
    ArticleReadLog,
    Block,
    Scrap,
)
from apps.core.permissions.scrap import ScrapPermission
from apps.core.serializers.scrap import (
    ScrapSerializer,
    ScrapCreateActionSerializer,
)


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
        ).select_related(
            'scrapped_by',
            'scrapped_by__profile',
            'parent_article',
            'parent_article__created_by',
            'parent_article__created_by__profile',
            'parent_article__parent_topic',
            'parent_article__parent_board',
        ).prefetch_related(
            'parent_article__comment_set',
            'parent_article__comment_set__comment_set',
            'parent_article__attachments',
            'parent_article__article_update_log_set',
            Block.prefetch_my_block(
                self.request.user,
                prefix='parent_article__'),
            ArticleReadLog.prefetch_my_article_read_log(
                self.request.user,
                prefix='parent_article__'),
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )
