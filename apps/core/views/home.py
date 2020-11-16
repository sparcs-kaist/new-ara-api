from rest_framework import views, response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from apps.core.models import BestArticle, PERIOD_CHOICES
from apps.core.serializers.article import BestArticleListActionSerializer


class HomeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return response.Response(data={
            'daily_bests': _best_articles('daily', request),
            'weekly_bests': _best_articles('weekly', request),
        })


def _best_articles(period, request):
    try:
        assert (period, period) in PERIOD_CHOICES
    except AssertionError:
        raise ValueError(f'Wrong period: {period}')

    return BestArticleListActionSerializer(
        instance=[
            best_article.article for best_article
            in BestArticle.objects.filter(period=period, latest=True).reverse()
        ],
        many=True,
        **{'context': {'request': request}},
    ).data
