from django.db.models import Q, QuerySet, TextChoices
from django_filters.rest_framework import CharFilter, ChoiceFilter, FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from apps.core.documents import ArticleDocument
from apps.core.models import Article
from apps.core.models.board import NameType


class ArticleSearchType(TextChoices):
    TITLE = "title", "제목"
    CONTENT = "content", "내용"
    TITLE_CONTENT = "title_content", "제목+내용"
    AUTHOR = "author", "작성자"


ARTICLE_SEARCH_PARAMETERS = [
    OpenApiParameter("main_search__contains", OpenApiTypes.STR, description="검색어"),
    OpenApiParameter(
        "search_type",
        OpenApiTypes.STR,
        enum=ArticleSearchType.values,
        description=(
            "제목/내용/제목+내용/작성자 검색 모드. 작성자는 공개 닉네임 부분 일치. "
            "생략하면 기존 검색 범위(일반: 제목+내용+닉네임, 과목/학과: 제목+내용)를 유지."
        ),
    ),
]


class ArticleSearchFilter(FilterSet):
    main_search__contains = CharFilter(label="검색어", method="search")
    search_type = ChoiceFilter(
        choices=ArticleSearchType.choices,
        label="검색 모드 (작성자는 공개 닉네임 부분 일치)",
        method="select_search_type",
    )

    @staticmethod
    def select_search_type(
        queryset: QuerySet[Article], name: str, value: str
    ) -> QuerySet[Article]:
        # 검색 모드는 검색어 필터에서 함께 적용한다.
        return queryset

    def search(
        self, queryset: QuerySet[Article], name: str, value: str
    ) -> QuerySet[Article]:
        keyword = value.strip()
        if not keyword:
            return queryset
        search_type = self.form.cleaned_data.get("search_type")
        if search_type == ArticleSearchType.AUTHOR:
            # 익명/실명 글을 실제 닉네임으로 역추적할 수 없도록 제한한다.
            return queryset.filter(
                name_type=NameType.REGULAR,
                created_by__profile__nickname__icontains=keyword,
            )
        if search_type == ArticleSearchType.TITLE:
            return queryset.filter(title__icontains=keyword)
        if search_type == ArticleSearchType.CONTENT:
            return queryset.filter(content_text__icontains=keyword)
        return queryset.filter(
            Q(title__icontains=keyword) | Q(content_text__icontains=keyword)
        )


class GeneralArticleSearchFilter(ArticleSearchFilter):
    def search(
        self, queryset: QuerySet[Article], name: str, value: str
    ) -> QuerySet[Article]:
        keyword = value.strip()
        if not keyword:
            return queryset
        search_type = self.form.cleaned_data.get("search_type")
        if search_type == ArticleSearchType.AUTHOR:
            return super().search(queryset, name, keyword)
        return queryset.filter(
            id__in=ArticleDocument.get_main_search_id_set(keyword, search_type or None)
        )


def filter_article_search(
    queryset: QuerySet[Article], request: Request, *, general: bool = False
) -> QuerySet[Article]:
    filter_class = GeneralArticleSearchFilter if general else ArticleSearchFilter
    search_filter = filter_class(
        request.query_params, queryset=queryset, request=request
    )
    if not search_filter.is_valid():
        raise ValidationError(search_filter.errors)
    return search_filter.qs
