from django.db import models

from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Article, \
    ArticleReadLog, ArticleUpdateLog, ArticleDeleteLog, Block, Comment, CommentUpdateLog, Report, Vote, Scrap
from apps.core.filters.article import ArticleFilter
from apps.core.permissions.article import ArticlePermission
from apps.core.serializers.article import ArticleSerializer, \
    ArticleListActionSerializer, ArticleCreateActionSerializer, ArticleUpdateActionSerializer


class ArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Article.objects.all()
    filter_class = ArticleFilter
    serializer_class = ArticleSerializer
    action_serializer_class = {
        'list': ArticleListActionSerializer,
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

        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        if self.action != 'list':
            # optimizing queryset for create, update, retrieve actions
            queryset = queryset.select_related(
                'created_by',
                'created_by__profile',
                'parent_topic',
                'parent_board',
            ).prefetch_related(
                Scrap.prefetch_my_scrap(self.request.user),
                models.Prefetch(
                    'comment_set',
                    queryset=Comment.objects.order_by('created_at').select_related(
                        'attachment',
                    ).prefetch_related(
                        Vote.prefetch_my_vote(self.request.user),
                        Block.prefetch_my_block(self.request.user),
                        Report.prefetch_my_report(self.request.user),
                        CommentUpdateLog.prefetch_comment_update_log_set(),
                        models.Prefetch(
                            'comment_set',
                            queryset=Comment.objects.order_by('created_at').select_related(
                                'attachment',
                            ).prefetch_related(
                                Vote.prefetch_my_vote(self.request.user),
                                Block.prefetch_my_block(self.request.user),
                                Report.prefetch_my_report(self.request.user),
                                CommentUpdateLog.prefetch_comment_update_log_set(),
                            ),
                        ),
                    ),
                ),
            )

        return queryset

    def paginate_queryset(self, queryset):
        # optimizing queryset for list action
        queryset = queryset.select_related(
            'created_by',
            'created_by__profile',
            'parent_topic',
            'parent_board',
        ).prefetch_related(
            Block.prefetch_my_block(self.request.user),
            ArticleReadLog.prefetch_my_article_read_log(self.request.user),
            ArticleUpdateLog.prefetch_article_update_log_set(),
        )

        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance

        ArticleUpdateLog.objects.create(
            updated_by=self.request.user,
            article=instance,
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
