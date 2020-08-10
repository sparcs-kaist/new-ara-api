from rest_framework import views, response
from apps.core.models import ArticleReadLog
from apps.core.serializers.article import ArticleListActionSerializer


class RecentView(views.APIView):
    def get(self, request):
        return response.Response(data={
            'recently_read': recently_read_articles(request)
        })


def recently_read_articles(request):
    return ArticleListActionSerializer(
        instance=[
            recent_article.article for recent_article
            in ArticleReadLog.objects.filter(read_by=request.user).all()[:5]
        ],
        many=True,
        **{'context': {'request': request}},
    ).data
