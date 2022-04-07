import time

from django.db import models
from django.http import Http404
from django.utils.translation import gettext
from rest_framework import status, viewsets, response, decorators, serializers, permissions
from rest_framework.response import Response
from apps.core.models.board import BoardNameType

from ara import redis
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import (
    Article,
    ArticleReadLog,
    ArticleUpdateLog,
    ArticleDeleteLog,
    Board,
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

from apps.core.documents import ArticleDocument


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

        if self.action == 'destroy':
            pass

        elif self.action == 'list':
            created_by = self.request.query_params.get('created_by')
            if created_by and int(created_by) != self.request.user.id:
                # exclude someone's anonymous or realname article in one's profile
                exclude_list = [BoardNameType.ANONYMOUS, BoardNameType.REALNAME]
                queryset = queryset.exclude(name_type__in=exclude_list)

            # exclude article written by blocked users in anonymous board
            queryset = queryset.exclude(
                created_by__id__in=self.request.user.block_set.values('user'),
                name_type=BoardNameType.ANONYMOUS
            )

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
            name_type=Board.objects.get(pk=self.request.data['parent_board']).name_type
        )

    def update(self, request, *args, **kwargs):
        article = self.get_object()
        if article.is_hidden_by_reported():
            return response.Response({'message': gettext('Cannot modify articles hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

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

    def destroy(self, request, *args, **kwargs):
        article = self.get_object()
        if article.is_hidden_by_reported():
            return response.Response({'message': gettext('Cannot delete articles hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        ArticleDeleteLog.objects.create(
            deleted_by=self.request.user,
            article=instance,
        )

        return super().perform_destroy(instance)

    def retrieve(self, request, *args, **kwargs):
        try:
            article = self.get_object()
        except Http404 as e:
            if Article.objects.queryset_with_deleted.filter(id=kwargs['pk']).exists():
                return response.Response(status=status.HTTP_410_GONE)
            else:
                raise e

        override_hidden = 'override_hidden' in self.request.query_params

        ArticleReadLog.objects.create(
            read_by=self.request.user,
            article=article,
        )

        article.update_hit_count()

        pipe = redis.pipeline()
        redis_key = 'articles:hit'
        pipe.zadd(redis_key, {f'{article.id}:1:{self.request.user.id}:{time.time()}': time.time()})
        pipe.execute(raise_on_error=True)

        serialized = ArticleSerializer(article, context={'request': request, 'override_hidden': override_hidden})
        return Response(serialized.data)

    @decorators.action(detail=True, methods=['post'])
    def vote_cancel(self, request, *args, **kwargs):
        article = self.get_object()

        if article.is_hidden_by_reported():
            return response.Response({'message': gettext('Cannot cancel vote on articles hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

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
            return response.Response({'message': gettext('Cannot vote on your own article')},
                                     status=status.HTTP_403_FORBIDDEN)

        if article.is_hidden_by_reported():
            return response.Response({'message': gettext('Cannot vote on articles hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

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
            return response.Response({'message': gettext('Cannot vote on your own article')},
                                     status=status.HTTP_403_FORBIDDEN)

        if article.is_hidden_by_reported():
            return response.Response({'message': gettext('Cannot vote on articles hidden by reports')},
                                     status=status.HTTP_403_FORBIDDEN)

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

        search_keyword = request.query_params.get('main_search__contains')
        search_restriction_sql = ''
        if search_keyword:
            id_set = ArticleDocument.get_main_search_id_set(search_keyword)
            if id_set:
                search_restriction_sql = 'AND `core_articlereadlog`.`article_id` IN %s'
            else:
                # There is no search result! Return empty result
                self.paginate_queryset(ArticleReadLog.objects.none())
                return self.paginator.get_paginated_response([])

        # Cardinality of this queryset is same with actual query
        count_queryset = ArticleReadLog.objects.values("article_id").filter(read_by=request.user).distinct()
        if search_keyword:
            count_queryset = count_queryset.filter(article_id__in=id_set)

        self.paginate_queryset(count_queryset)

        query_params = [self.request.user.id, self.paginator.get_page_size(request), max(0, self.paginator.page.start_index()-1)]
        if search_keyword:
            query_params.insert(1, id_set)

        queryset = Article.objects.raw(
            f'''
            SELECT * FROM `core_article`
            JOIN (
                SELECT `core_articlereadlog`.`article_id`, MAX(`core_articlereadlog`.`created_at`) AS my_last_read_at
                FROM `core_articlereadlog`
                WHERE (`core_articlereadlog`.`deleted_at` = '0001-01-01 00:00:00' AND `core_articlereadlog`.`read_by_id` = %s {search_restriction_sql})
                GROUP BY `core_articlereadlog`.`article_id`
                ORDER BY my_last_read_at desc
                LIMIT %s OFFSET %s
            ) recents ON recents.article_id = `core_article`.id
            ORDER BY recents.my_last_read_at desc
            ''', 
            query_params
        ).prefetch_related(
            'created_by',
            'created_by__profile',
            'parent_board',
            'parent_topic',
            ArticleReadLog.prefetch_my_article_read_log(self.request.user)
        )

        serializer = self.get_serializer_class()([v for v in queryset], many=True, context={"request": request})
        return self.paginator.get_paginated_response(serializer.data)
