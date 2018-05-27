from rest_framework import views, response

from apps.core.models import BestArticle, Board, PERIOD_CHOICES, BEST_BY_CHOICES
from apps.core.serializers.article import ArticleSerializer
from apps.core.serializers.board import BoardRecentArticleActionSerializer


class HomeView(views.APIView):
    def get(self, request, format=None):
        return response.Response(data={
            'daily_bests': {
                'positive_vote_count': _best_articles('daily', 'positive_vote_count', request),
                'hit_count': _best_articles('daily', 'hit_count', request),
            },
            'weekly_bests': {
                'positive_vote_count': _best_articles('weekly', 'positive_vote_count', request),
                'hit_count': _best_articles('weekly', 'hit_count', request),
            },
            'boards': BoardRecentArticleActionSerializer(
                instance=Board.objects.prefetch_related('article_set'),
                many=True,
                **{'context': {'request': request}},
            ).data
        })


def _best_articles(period, best_by, request):
    try:
        assert (period, period) in PERIOD_CHOICES and (best_by, best_by) in BEST_BY_CHOICES
    except AssertionError:
        raise ValueError(f'Wrong period or best_by: {period} / {best_by}')

    return ArticleSerializer(
        instance=[
            best_article.article for best_article
            in BestArticle.objects.filter(period=period, best_by=best_by).order_by('-id')[:5]
        ],
        many=True,
        **{'context': {'request': request}},
    ).data
