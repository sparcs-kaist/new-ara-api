from django_filters.rest_framework import BooleanFilter, FilterSet

from apps.core.models import Notification


class NotificationFilter(FilterSet):
    class Meta:
        model = Notification
        fields = {
            "type": [
                "in",
                "exact",
            ],
            "title": [
                "contains",
            ],
            "content": [
                "contains",
            ],
            "related_article": [
                "in",
                "exact",
            ],
            "related_comment": [
                "in",
                "exact",
            ],
        }

    is_read = BooleanFilter(
        field_name="is_read",
        label="조회 여부",
        method="get_is_read",
    )

    @staticmethod
    def get_is_read(queryset, field_name, value):
        return queryset.filter(
            notification_read_log_set__is_read=value,
        )
