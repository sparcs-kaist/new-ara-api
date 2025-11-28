from datetime import timedelta
from django.utils import timezone
from django.db.models import Subquery, OuterRef, F, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework import decorators

from apps.kaist.models import Post, PostViewCountLog
from apps.kaist.serializers.trending_posts import TrendingPostsSerializer

class PortalNoticeView(viewsets.ModelViewSet):

    def list(self, request):
        """게시판 번호와 limit으로 공지사항 조회"""
        board = request.query_params.get('board')
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        queryset = Post.objects.all()
        
        if board:
            queryset = queryset.filter(board_id=board)
        
        queryset = queryset.order_by('-registered_at')[:limit]
        
        serializer = TrendingPostsSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #최근 24시간 동안 조회수 증가량이 가장 많은 게시물 조회
    @decorators.action(detail=True, methods=["get"])
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