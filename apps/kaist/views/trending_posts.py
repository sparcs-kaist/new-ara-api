from datetime import timedelta
from django.utils import timezone
from django.db.models import Subquery, OuterRef, F, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.kaist.models import Post, PostViewCountLog
from apps.kaist.serializers.trending_posts import TrendingPostsSerializer

class TrendingPostsView(APIView):
    """
    최근 24시간 동안 조회수가 가장 많이 상승한 게시물 5개 조회
    """
    def get(self, request):
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