from rest_framework import views, response
from apps.core.models import ArticleReadLog
from apps.core.serializers.article import ArticleListActionSerializer


class RecentView(views.APIView):
    def get(self, request):
        return response.Response(data={
            'recently_read': recently_read_articles(request)
        })

# TODO: 한 article을 한번만 읽으면 created_at은 읽은 시각, 그리고 updated_at이 mintime이기 때문에,
#  ordered_by를 updated_at이나 created_by에 사용하면 저희가 원하는, 최근 읽은 순으로 나오지 않습니다.
#  그래서 sorted를 사용해서, last_read_at property로 sorting 했는데, 이렇게 하면 느리다는 의견이 있습니다.
#  sorted로 해도 속도가 괜찮을지 확인 부탁드립니다.


# 이 사용자가 이제까지 읽은 모든 article을 리턴함
# 리턴 타입: List[OrderedDict], 0번쨰 element가 가장 최근에 읽은 article
# 최근 n개만 가져오기위해서는, 4번쨰 줄을 다음과 같이 수정: in ArticleReadLog.objects.filter(read_by=request.user).all()[:n]
def recently_read_articles(request):
    recent_articles = ArticleReadLog.objects.filter(read_by=request.user).all()
    sorted_recent_articles = sorted(recent_articles, key=lambda t: t.last_read_at, reverse=True)
    return ArticleListActionSerializer(
        instance=[
            recent_article.article for recent_article
            in sorted_recent_articles
        ],
        many=True,
        **{'context': {'request': request}},
    ).data
