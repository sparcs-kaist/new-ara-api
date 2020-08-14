from django.db.models import Case, When
from rest_framework import views, response
from apps.core.models import ArticleReadLog, datetime
from apps.core.serializers.article import ArticleListActionSerializer
from ara.classes.pagination import PageNumberPagination


class RecentView(views.APIView):
    def get(self, request):
        return response.Response(data={
            'recently_read': recently_read_articles(request)
        })


def recently_read_articles(request):
    paginator = PageNumberPagination()
    recent_read_at = Case(When(updated_at=datetime.datetime.min, then='created_at'), default='updated_at')
    recent_articles = ArticleReadLog.objects \
        .filter(read_by=request.user) \
        .annotate(recent_read_at=recent_read_at) \
        .order_by('-recent_read_at')
    result_page = paginator.paginate_queryset(recent_articles, request)

    return ArticleListActionSerializer(
        instance=[v.article for v in result_page],
        many=True,
        context={'request': request}
    ).data
