from rest_framework import views, response

from apps.core.models import BestArticle, BestComment, Board
from apps.core.serializers.article import ArticleSerializer
from apps.core.serializers.comment import CommentSerializer
from apps.core.serializers.board import BoardRecentArticleActionSerializer


class HomeView(views.APIView):
    def get(self, request, format=None):
        return response.Response(data={
            'best_articles': ArticleSerializer(
                instance=[
                    best_article.article for best_article in BestArticle.objects.order_by('-id')[:5]
                ],
                many=True,
            ).data,
            'best_comments': CommentSerializer(
                instance=[
                    best_comment.comment for best_comment in BestComment.objects.order_by('-id')[:5]
                ],
                many=True,
            ).data,
            'boards': BoardRecentArticleActionSerializer(
                instance=Board.objects.prefetch_related('article_set'),
                many=True,
            ).data,
        })
