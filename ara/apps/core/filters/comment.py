import rest_framework_filters as filters

from apps.core.models import Comment


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Article
        fields = {
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
        }
