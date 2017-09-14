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
            'parent_topic': [
                'in',
                'exact',
            ],
            'parent_board': [
                'in',
                'exact',
            ],
        }
