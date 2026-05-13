from rest_framework import response, views
from rest_framework.permissions import IsAuthenticated

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

    # 과목/학과게시판 글은 same-major / enrolled 사용자만 봐야 하므로 메인
    # home 의 best 에서 제외. _get_best 는 Redis vote/hit 로 top 5 를 뽑는데,
    # 과목/학과글 vote 도 같은 키에 들어가서 BestArticle 에 섞일 수 있다.
    # 표시 단계에서 안전망으로 필터.
    return BestArticleListActionSerializer(
        instance=[
            best_article.article
            for best_article in BestArticle.objects.filter(
                period=period,
                latest=True,
                article__related_course__isnull=True,
                article__related_major__isnull=True,
            )
            .select_related("article")
            .reverse()
        ],
        many=True,
        **{"context": {"request": request}},
    ).data
