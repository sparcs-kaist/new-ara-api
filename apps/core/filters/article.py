from django.db import models

import rest_framework_filters as filters

from apps.core.documents import ArticleDocument
from apps.core.models import Article


class ArticleFilter(filters.FilterSet):
    class Meta:
        model = Article
        fields = {
            'title': [
                'contains',
            ],
            'content': [
                'contains',
            ],
            'content_text': [
                'contains',
            ],
            'is_anonymous': [
                'exact',
            ],
            'is_content_sexual': [
                'exact',
            ],
            'is_content_social': [
                'exact',
            ],
            'created_by': [
                'exact',
            ],
            'created_by__username': [
                'exact',
                'contains',
            ],
            'created_by__profile__nickname': [
                'exact',
                'contains',
            ],
            'parent_topic': [
                'in',
                'exact',
            ],
            'parent_board': [
                'in',
                'exact',
            ],
        }

    main_search__contains = filters.CharFilter(
        field_name='main_search',
        label='메인 검색 (제목포함, 본문포함, 닉네임일치)',
        method='get_main_search__contains'
    )

    @staticmethod
    def get_main_search__contains(queryset, name, value):

        title_articles = Article.objects.filter(id__in=ArticleDocument.get_id_set('title', value))
        content_articles = Article.objects.filter(id__in=ArticleDocument.get_id_set('content_text', value))
        nickname_articles = Article.objects.filter(id__in=ArticleDocument.get_id_set('created_by_nickname', value))
        qs = title_articles | content_articles | nickname_articles

        return qs.distinct()
