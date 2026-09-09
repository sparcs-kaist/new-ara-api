from rest_framework import response, views
from rest_framework.permissions import IsAuthenticated

from apps.core.article_scope import exclude_scoped_articles
from apps.core.models import PERIOD_CHOICES, BestArticle
from apps.core.serializers.article import BestArticleListActionSerializer


class HomeView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return response.Response(
            data={
                "daily_bests": _best_articles("daily", request),
                "weekly_bests": _best_articles("weekly", request),
            }
        )


def _best_articles(period, request) -> dict:
    try:
        assert (period, period) in PERIOD_CHOICES
    except AssertionError:
        raise ValueError(f"Wrong period: {period}")

    # Redis vote/hit keys에는 scoped article도 포함되므로 main home의 best 결과에서 제외한다.
    return BestArticleListActionSerializer(
        instance=[
            best_article.article
            for best_article in exclude_scoped_articles(
                BestArticle.objects.filter(period=period, latest=True),
                prefix="article",
            )
            .select_related("article")
            .reverse()
        ],
        many=True,
        **{"context": {"request": request}},
    ).data
