import rest_framework_filters as filters

from apps.core.models import Board


class BoardFilter(filters.FilterSet):
    class Meta:
        model = Board
        fields = {
            'is_readonly': [
                'exact',
            ],
        }
