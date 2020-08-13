from django.db import models

import rest_framework_filters as filters

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

    title_or_content__contains = filters.CharFilter(
        field_name='title_or_content__contains',
        label='제목 or 본문 contains',
        method='get_title_or_content__contains',
    )

    title_or_content_text__contains = filters.CharFilter(
        field_name='title_or_content_text__contains',
        label='제목 or 본문 contains',
        method='get_title_or_content_text__contains',
    )

    main_search__contains = filters.CharFilter(
        field_name='main_search',
        label='메인 검색 (제목포함, 본문포함, 닉네임일치)',
        method='get_main_search__contains'
    )

    @staticmethod
    def get_title_or_content__contains(queryset, name, value):
        return queryset.filter(
            models.Q(title__contains=value) |
            models.Q(content__contains=value)
        ).distinct()

    @staticmethod
    def get_title_or_content_text__contains(queryset, name, value):
        return queryset.filter(
            models.Q(title__contains=value) |
            models.Q(content_text__contains=value)
        ).distinct()

    @staticmethod
    def get_main_search__contains(queryset, name, value):
        return queryset.filter(
            models.Q(title__contains=value) |
            models.Q(content_text__contains=value) |
            models.Q(created_by__profile__nickname__contains=value)
        ).distinct()
