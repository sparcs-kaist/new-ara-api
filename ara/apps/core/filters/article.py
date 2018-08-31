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

    title_or_contents_contains = filters.CharFilter(
        name='title_or_contents_contains',
        label='제목 or 본문 contains',
        method='get_title_or_contents_contains',
    )

    @staticmethod
    def get_title_or_contents_contains(queryset, name, value):
        return queryset.filter(
            models.Q(title=value) |
            models.Q(content=value)
        ).distinct()
