from django.db.models import Case, When
from rest_framework import views, response
from apps.core.models import ArticleReadLog, Block, datetime
from apps.core.serializers.article import ArticleListActionSerializer
from ara.classes.pagination import PageNumberPagination


class RecentView(views.APIView):
    def get(self, request):
        return response.Response(data={
            'recently_read': recently_read_articles(request)
        })


def recently_read_articles(request):
    paginator = PageNumberPagination()
    recent_articles = ArticleReadLog.objects.filter(
        read_by=request.user
    ).order_by('-updated_at'
               ).select_related('article', 'article__created_by',
                                'article__created_by__profile',
                                'article__parent_topic',
                                'article__parent_board',
                                ).prefetch_related('article__comment_set',
                                                   'article__comment_set__comment_set',
                                                   'article__attachments',
                                                   'article__article_update_log_set',
                                                   Block.prefetch_my_block(request.user, prefix='article__'))

    result_page = paginator.paginate_queryset(recent_articles, request)

    return ArticleListActionSerializer(
        instance=[v.article for v in result_page],
        many=True,
        context={'request': request}
    ).data
