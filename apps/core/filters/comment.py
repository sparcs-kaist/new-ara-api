from django_filters.rest_framework import FilterSet

from apps.core.models import Comment


class CommentFilter(FilterSet):
    class Meta:
        model = Comment
        fields = {
            "content": [
                "contains",
            ],
            "parent_article": [
                "exact",
            ],
            "parent_comment": [
                "exact",
            ],
            "name_type": [
                "exact",
            ],
            "created_by": [
                "exact",
            ],
        }
