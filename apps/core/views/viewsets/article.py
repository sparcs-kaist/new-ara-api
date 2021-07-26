import time

from django.db import models
from rest_framework import status, viewsets, response, decorators, serializers, permissions
from rest_framework.response import Response

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
        'recent': ArticleListActionSerializer,
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

        if self.action == 'list':
            created_by = self.request.query_params.get('created_by')
            if created_by is not None:  # 특정 사용자의 글을 가져오는 쿼리
                created_by = int(created_by)
                if created_by != self.request.user.id:  # 사용자가 다른 사람의 글들을 가져올 때 (ex. 사용자 이름 클릭해서)
                    # 다른 사용자의 글들을 볼때는, 익명 글 숨기기
                    queryset = queryset.exclude(is_anonymous=1)

            # optimizing queryset for list action
            queryset = queryset.select_related(
                'created_by',
                'created_by__profile',
                'parent_topic',
                'parent_board',
            ).prefetch_related(
                ArticleReadLog.prefetch_my_article_read_log(self.request.user),
            )

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

        serialized = self.serializer_class(article, context={'request': request})
        return Response(serialized.data)

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
        # Cardinality of this queryset is same with actual query
        count_queryset = ArticleReadLog.objects \
            .values("article_id") \
            .filter(read_by=request.user) \
            .distinct()

        self.paginate_queryset(count_queryset)

        queryset = Article.objects.raw('''
            SELECT * FROM `core_article`
            JOIN (
                SELECT `core_articlereadlog`.`article_id`, MAX(`core_articlereadlog`.`created_at`) AS my_last_read_at
                FROM `core_articlereadlog`
                WHERE (`core_articlereadlog`.`deleted_at` = '0001-01-01 00:00:00' AND `core_articlereadlog`.`read_by_id` = %s)
                GROUP BY `core_articlereadlog`.`article_id`
                ORDER BY my_last_read_at desc
                LIMIT %s OFFSET %s
            ) recents ON recents.article_id = `core_article`.id
            ''', [self.request.user.id, self.paginator.get_page_size(request), max(0, self.paginator.page.start_index()-1)]) \
            .prefetch_related('created_by',
                              'created_by__profile',
                              'parent_board',
                              'parent_topic',
                              ArticleReadLog.prefetch_my_article_read_log(self.request.user))

        serializer = self.get_serializer_class()([v for v in queryset], many=True, context={"request": request})
        return self.paginator.get_paginated_response(serializer.data)
