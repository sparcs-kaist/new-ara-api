from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Article, ArticleReadLog, ArticleUpdateLog, ArticleDeleteLog, Vote, Block
from apps.core.filters.article import ArticleFilter
from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.article import ArticleSerializer, ArticleDetailActionSerializer, \
    ArticleCreateActionSerializer, ArticleUpdateActionSerializer


class ArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Article.objects.select_related(
        'created_by',
        'parent_topic',
        'parent_board',
    )
    filter_class = ArticleFilter
    serializer_class = ArticleSerializer
    action_serializer_class = {
        'retrieve': ArticleDetailActionSerializer,
        'create': ArticleCreateActionSerializer,
        'update': ArticleUpdateActionSerializer,
        'partial_update': ArticleUpdateActionSerializer,
        'vote_positive': serializers.Serializer,
        'vote_negative': serializers.Serializer,
    }
    permission_classes = (
        ArticlePermission,
    )
    action_permission_classes = {
        'vote_cancel': (
            permissions.IsAuthenticated,
        ),
        'vote_positive': (
            permissions.IsAuthenticated,
        ),
        'vote_negative': (
            permissions.IsAuthenticated,
        ),
    }

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'best':
            queryset = queryset.filter(
                best__isnull=False,
            )

        if not self.request.user.profile.see_sexual:
            queryset = queryset.filter(
                is_content_sexual=False,
            )

        if not self.request.user.profile.see_social:
            queryset = queryset.filter(
                is_content_social=False,
            )

        queryset = queryset.exclude(
            created_by__in=[block.user for block in Block.objects.filter(blocked_by=self.request.user)]
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance

        ArticleUpdateLog.objects.create(
            updated_by=self.request.user,
            article=instance,
            content=instance.content,
            is_content_sexual=instance.is_content_sexual,
            is_content_social=instance.is_content_social,
            use_signature=instance.use_signature,
            parent_topic=instance.parent_topic,
            parent_board=instance.parent_board,
        )

        return super().perform_update(serializer)

    def perform_destroy(self, instance):
        ArticleDeleteLog.objects.create(
            deleted_by=self.request.user,
            article=instance,
        )

        return super().perform_destroy(instance)

    def retrieve(self, request, *args, **kwargs):
        article = self.get_object()

        article_read_log, created = ArticleReadLog.objects.update_or_create(
            read_by=self.request.user,
            article=article,
        )

        if created:
            article.update_hit_count()

        return super().retrieve(request, *args, **kwargs)

    @decorators.list_route(methods=['get'])
    def best(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @decorators.detail_route(methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        article = self.get_object()

        Vote.objects.filter(
            voted_by=request.user,
            parent_article=article,
        ).delete()

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        article = self.get_object()

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': True,
            },
        )

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_negative(self, request, *args, **kwargs):
        article = self.get_object()

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': False,
            },
        )

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
