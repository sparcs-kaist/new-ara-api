from datetime import timedelta
from django.utils import timezone
from django.db.models import Subquery, OuterRef, F, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework import status
from rest_framework import decorators
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.kaist.models import Post, PostViewCountLog
from apps.kaist.serializers.trending_posts import TrendingPostsSerializer

class PortalNoticeView(viewsets.GenericViewSet):

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='board',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='게시판 번호 (board_id)',
                required=False,
            ),
        ],
        responses={200: TrendingPostsSerializer(many=True)},
        summary='포탈 공지사항 목록 조회',
    )
    def list(self, request):
        """게시판 번호와 limit으로 공지사항 조회"""
        board = request.query_params.get('board')
        queryset = Post.objects.all()
        
        if board:
            queryset = queryset.filter(board_id=board)
        
        queryset = queryset.order_by('-registered_at')
        
        serializer = TrendingPostsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #최근 24시간 동안 조회수 증가량이 가장 많은 게시물 조회
    @decorators.action(detail=False, methods=["get"])
    def trending(self, request):
        now = timezone.now()
        time_24_hours_ago = now - timedelta(hours=24)
        search_range_start = now - timedelta(days=7)

        # 각 게시물의 24시간 전 시점(혹은 그 이전에 생성된 것 중 가장 최신)의 조회수 로그 찾는 쿼리
        past_log_qs = PostViewCountLog.objects.filter(
            post=OuterRef('pk'),
            created_at__lte=time_24_hours_ago
        ).order_by('-created_at').values('view_count')[:1]

        trending_posts = Post.objects.filter(
            registered_at__gte=search_range_start
        ).annotate(
            # 24시간 전 조회수 로그 (없으면 0)
            past_view_count=Coalesce(
                Subquery(past_log_qs), 
                Value(0), 
                output_field=IntegerField()
            ),
            view_count_growth=F('view_count') - F('past_view_count')
        ).order_by('-view_count_growth')[:5]

        serializer = TrendingPostsSerializer(trending_posts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='ara_article',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='아라 게시글 ID (ara_article)',
                required=True,
            ),
        ],
        responses={200: TrendingPostsSerializer()},
        summary='아라 게시글 ID로 포탈 공지 조회',
    )
    @decorators.action(detail=False, methods=["get"])
    def by_article(self, request):
        """ara_article ID로 해당하는 Post 하나 조회"""
        ara_article_id = request.query_params.get('ara_article')
        
        if not ara_article_id:
            return Response(
                {"error": "ara_article parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            post = Post.objects.get(ara_article_id=ara_article_id)
            serializer = TrendingPostsSerializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response(
                {"error": "Post not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )