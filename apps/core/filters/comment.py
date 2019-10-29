import rest_framework_filters as filters

from apps.core.models import Comment


class CommentFilter(filters.FilterSet):
    class Meta:
        model = Comment
        fields = {
            'content': [
                'contains',
            ],
            'parent_article': [
                'exact',
            ],
            'parent_comment': [
                'exact',
            ],
            'is_anonymous': [
                'exact',
            ],
            'created_by': [
                'exact',
            ],
        }
