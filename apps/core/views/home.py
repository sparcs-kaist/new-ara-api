from rest_framework import views, response

from apps.core.models import BestArticle, PERIOD_CHOICES, BEST_BY_CHOICES
from apps.core.serializers.article import ArticleListActionSerializer


class HomeView(views.APIView):
    def get(self, request):
        return response.Response(data={
            'daily_bests': _best_articles('daily', 'positive_vote_count', request),
            'weekly_bests': _best_articles('weekly', 'positive_vote_count', request),
        })


def _best_articles(period, best_by, request):
    try:
        assert (period, period) in PERIOD_CHOICES and (
            best_by, best_by) in BEST_BY_CHOICES
    except AssertionError:
        raise ValueError(
            'Wrong period or best_by: {} / {}'.format(period, best_by))

    return ArticleListActionSerializer(
        instance=[
            best_article.article for best_article
            in BestArticle.objects.filter(period=period, best_by=best_by).all()[:5]
        ],
        many=True,
        **{'context': {'request': request}},
    ).data
