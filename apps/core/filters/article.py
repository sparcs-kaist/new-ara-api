from __future__ import annotations

from typing import TYPE_CHECKING

from django_filters.rest_framework import CharFilter, FilterSet

from apps.core.documents import ArticleDocument
from apps.core.models import Article

if TYPE_CHECKING:
    from ara.db.models import MetaDataQuerySet


class ArticleFilter(FilterSet):
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

    main_search__contains = CharFilter(
        field_name="main_search",
        label="메인 검색 (제목포함, 본문포함, 닉네임일치)",
        method="get_main_search__contains",
    )

    @staticmethod
    def get_main_search__contains(
        queryset: MetaDataQuerySet, name: str, value: str
    ) -> MetaDataQuerySet:
        return queryset.filter(id__in=ArticleDocument.get_main_search_id_set(value))
