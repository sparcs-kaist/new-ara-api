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
    Comment,
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

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # optimizing queryset for list action
        if self.action in ['list', 'recent']:
            queryset = queryset.select_related(
                'created_by',
                'created_by__profile',
                'parent_topic',
                'parent_board',
            ).prefetch_related(
                ArticleReadLog.prefetch_my_article_read_log(self.request.user),
            )

            # optimizing queryset for recent action
            if self.action == 'recent':
                last_read_log_of_the_article = ArticleReadLog.objects.filter(
                    article=models.OuterRef('pk')
                ).order_by('-created_at')

                queryset = queryset.filter(
                    article_read_log_set__read_by=self.request.user,
                ).annotate(
                    my_last_read_at=models.Subquery(last_read_log_of_the_article.filter(
                        read_by=self.request.user,
                    ).values('created_at')[:1]),
                ).order_by(
                    '-my_last_read_at'
                ).distinct()

        # optimizing queryset for create, update, retrieve actions
        else:
            queryset = queryset.select_related(
                'created_by',
                'created_by__profile',
                'parent_topic',
                'parent_board',
            ).prefetch_related(
                'attachments',
                models.Prefetch(
                    'vote_set',
                    queryset=Vote.objects.select_related(
                        'voted_by',
                    ),
                ),
                Scrap.prefetch_my_scrap(self.request.user),
                models.Prefetch(
                    'comment_set',
                    queryset=Comment.objects.reverse().select_related(
                        'created_by',
                        'created_by__profile',
                    ).prefetch_related(
                        Vote.prefetch_my_vote(self.request.user),
                        models.Prefetch(
                            'comment_set',
                            queryset=Comment.objects.reverse().select_related(
                                'created_by',
                                'created_by__profile',
                            ).prefetch_related(
                                Vote.prefetch_my_vote(self.request.user),
                            ),
                        ),
                    ),
                ),
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
        )

    def perform_update(self, serializer):
        instance = serializer.instance

        update_log = ArticleUpdateLog.objects.create(
            updated_by=self.request.user,
            article=instance,
        )

        serializer.save(
            content_updated_at=update_log.created_at,
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

        ArticleReadLog.objects.create(
            read_by=self.request.user,
            article=article,
        )

        article.update_hit_count()

        pipe = redis.pipeline()
        redis_key = 'articles:hit'
        pipe.zadd(redis_key, {f'{article.id}:1:{self.request.user.id}:{time.time()}': time.time()})
        pipe.execute(raise_on_error=True)

        return super().retrieve(request, *args, **kwargs)

    @decorators.action(detail=True, methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        article = self.get_object()

        if not Vote.objects.filter(
            voted_by=request.user,
            parent_article=article,
        ).exists():
            return response.Response(status=status.HTTP_200_OK)

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

    @decorators.action(detail=False, methods=['get'])
    def recent(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
