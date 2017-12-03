from datetime import datetime

from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Article, ArticleReadLog, ArticleUpdateLog
from apps.core.filters.article import ArticleFilter
from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.article import ArticleSerializer, ArticleDetailActionSerializer, ArticleCreateActionSerializer, ArticleUpdateActionSerializer


class ArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Article.objects.all()
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
        'vote_positive': (
            permissions.IsAuthenticated,
        ),
        'vote_negative': (
            permissions.IsAuthenticated,
        ),
    }

    def get_queryset(self):
        queryset = super(ArticleViewSet, self).get_queryset()

        if self.action == 'best':
            queryset = queryset.filter(
                best__isnull=False,
            )

        user = self.request.user
        if user.profile.see_sexual == False:
            queryset = queryset.filter(
                is_content_sexual=False,
            )
        if user.profile.see_social == False:
            queryset = queryset.filter(
                is_content_social=False,
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance

        ArticleUpdateLog.objects.create(
            updated_by=instance.created_by,
            article=instance,
            content=instance.content,
            is_content_sexual=instance.is_content_sexual,
            is_content_social=instance.is_content_social,
            use_signature=instance.use_signature,
            parent_topic=instance.parent_topic,
            parent_board=instance.parent_board,
        )

        return super(ArticleViewSet, self).perform_update(serializer)

    def retrieve(self, request, *args, **kwargs):
        article_read_log, created = ArticleReadLog.objects.get_or_create(
            read_by=self.request.user,
            article=self.get_object(),
        )

        if not created:
            article_read_log.created_at = datetime.now()
            article_read_log.save()

        return super(ArticleViewSet, self).retrieve(request, *args, **kwargs)

    @decorators.list_route(methods=['get'])
    def best(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    @decorators.detail_route(methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        from apps.core.models import Vote

        article = self.get_object()

        vote, created = Vote.objects.get_or_create(
            created_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': True,
            },
        )

        if not created:
            vote.is_positive = True
            vote.save()

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_negative(self, request, *args, **kwargs):
        from apps.core.models import Vote

        article = self.get_object()

        vote, created = Vote.objects.get_or_create(
            created_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': False,
            },
        )

        if not created:
            vote.is_positive = False
            vote.save()

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)

    @decorators.detail_route(methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        from apps.core.models import Vote

        article = self.get_object()

        Vote.objects.filter(
            created_by=request.user,
            parent_article=article,
        ).delete()

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
