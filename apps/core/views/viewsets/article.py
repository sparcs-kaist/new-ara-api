import time

from django.db import models

from rest_framework import status, viewsets, response, decorators, serializers, permissions

from ara import redis
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import (
    Article,
    ArticleReadLog,
    ArticleUpdateLog,
    ArticleDeleteLog,
    Block,
    Comment,
    Report,
    Vote,
    Scrap,
)
from apps.core.filters.article import ArticleFilter
from apps.core.permissions.article import ArticlePermission, ArticleKAISTPermission
from apps.core.serializers.article import (
    ArticleSerializer,
    ArticleListActionSerializer,
    ArticleCreateActionSerializer,
    ArticleUpdateActionSerializer,
)


class ArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Article.objects.all()
    filterset_class = ArticleFilter
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
        ArticleKAISTPermission
    )
    action_permission_classes = {
        'vote_cancel': (
            permissions.IsAuthenticated,
            ArticleKAISTPermission
        ),
        'vote_positive': (
            permissions.IsAuthenticated,
            ArticleKAISTPermission
        ),
        'vote_negative': (
            permissions.IsAuthenticated,
            ArticleKAISTPermission
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
            # cacheops 이용으로 select_related에서 prefetch_related로 옮김
            queryset = queryset.select_related(
            ).prefetch_related(
                'created_by',
                'created_by__profile',
                'parent_topic',
                'parent_board',
                'attachments',
                Scrap.prefetch_my_scrap(self.request.user),
                Block.prefetch_my_block(self.request.user),
                models.Prefetch(
                    'comment_set',
                    queryset=Comment.objects.reverse().select_related(
                        'attachment',
                    ).prefetch_related(
                        'comment_update_log_set',
                        Vote.prefetch_my_vote(self.request.user),
                        Block.prefetch_my_block(self.request.user),
                        Report.prefetch_my_report(self.request.user),
                        models.Prefetch(
                            'comment_set',
                            queryset=Comment.objects.reverse().select_related(
                                'attachment',
                            ).prefetch_related(
                                'comment_update_log_set',
                                Vote.prefetch_my_vote(self.request.user),
                                Block.prefetch_my_block(self.request.user),
                                Report.prefetch_my_report(self.request.user),
                            ),
                        ),
                    ),
                ),
            )

        return queryset

    def paginate_queryset(self, queryset):
        # optimizing queryset for list action
        # cacheops 이용으로 select_related에서 prefetch_related로 옮김
        queryset = queryset.select_related(
        ).prefetch_related(
            'created_by',
            'created_by__profile',
            'parent_topic',
            'parent_board',
            'attachments',
            'article_update_log_set',
            Block.prefetch_my_block(self.request.user),
            ArticleReadLog.prefetch_my_article_read_log(self.request.user),
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

        created = ArticleReadLog.objects.update_or_create(
            read_by=self.request.user,
            article=article,
        )[1]

        if created:
            article.update_hit_count()

        pipe = redis.pipeline()
        redis_key = 'articles:hit'
        pipe.zadd(redis_key, {f'{article.id}:1:{self.request.user.id}:{time.time()}': time.time()})
        pipe.execute(raise_on_error=True)

        return super().retrieve(request, *args, **kwargs)

    @decorators.action(detail=True, methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        article = self.get_object()

        vote = Vote.objects.get(
            voted_by=request.user,
            parent_article=article,
        )
        vote.delete()

        article.update_vote_status()

        if vote.is_positive:
            pipe = redis.pipeline()
            redis_key = 'articles:vote'
            pipe.zadd(redis_key, {f'{article.id}:-1:{request.user.id}:{time.time()}': time.time()})
            pipe.execute(raise_on_error=True)

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['post'])
    def vote_positive(self, request, *args, **kwargs):
        article = self.get_object()

        if article.created_by_id == request.user.id:
            return response.Response({'message': '본인 글에는 좋아요를 누를 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': True,
            },
        )

        article.update_vote_status()

        pipe = redis.pipeline()
        redis_key = 'articles:vote'
        pipe.zadd(redis_key, {f'{article.id}:1:{request.user.id}:{time.time()}': time.time()})
        pipe.execute(raise_on_error=True)

        return response.Response(status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['post'])
    def vote_negative(self, request, *args, **kwargs):
        article = self.get_object()

        if article.created_by_id == request.user.id:
            return response.Response({'message': '본인 글에는 싫어요를 누를 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        Vote.objects.update_or_create(
            voted_by=request.user,
            parent_article=article,
            defaults={
                'is_positive': False,
            },
        )

        article.update_vote_status()

        return response.Response(status=status.HTTP_200_OK)
