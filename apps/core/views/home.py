from rest_framework import views, response

from apps.core.models import BestArticle, PERIOD_CHOICES, Article, Block
from apps.core.serializers.article import BestArticleListActionSerializer


class HomeView(views.APIView):
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

    best_ids = [
        best_article.article.id for best_article
        in BestArticle.objects.filter(period=period, latest=True)
    ]

    bests = Article.objects.filter(id__in=best_ids).prefetch_related(Block.prefetch_my_block(request.user))

    return BestArticleListActionSerializer(
        instance=bests,
        many=True,
        **{'context': {'request': request}},
    ).data
