from django_filters.rest_framework import CharFilter

from apps.core.filters.article_search import GeneralArticleSearchFilter
from apps.core.models import Article


class ArticleFilter(GeneralArticleSearchFilter):
    board = CharFilter(field_name="parent_board__slug", lookup_expr="exact")

    class Meta:
        model = Article
        fields = {
            "title": [
                "contains",
            ],
            "content": [
                "contains",
            ],
            "content_text": [
                "contains",
            ],
            "name_type": [
                "exact",
            ],
            "is_content_sexual": [
                "exact",
            ],
            "is_content_social": [
                "exact",
            ],
            "created_by": [
                "exact",
            ],
            "created_by__username": [
                "exact",
                "contains",
            ],
            "created_by__profile__nickname": [
                "exact",
                "contains",
            ],
            "parent_topic": [
                "in",
                "exact",
            ],
            "parent_board": [
                "in",
                "exact",
            ],
            "communication_article__school_response_status": [
                "exact",
                "lt",
            ],
        }
