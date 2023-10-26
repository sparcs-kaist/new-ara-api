from collections import OrderedDict

from django.core.paginator import InvalidPage
from rest_framework import pagination, response
from rest_framework.exceptions import NotFound


class PageNumberPagination(pagination.PageNumberPagination):
    page_size_query_param = "page_size"

    # Originated from rest_framework.pagination.PageNumberPagination
    def paginate_queryset(self, queryset, request, view=None, paginator_class=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator_class = (
            paginator_class if paginator_class else self.django_paginator_class
        )
        paginator = paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            raise NotFound(msg)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        return response.Response(
            OrderedDict(
                [
                    ("num_pages", self.page.paginator.num_pages),
                    ("num_items", self.page.paginator.count),
                    ("current", self.page.number),
                    ("previous", self.get_previous_link()),
                    ("next", self.get_next_link()),
                    ("results", data),
                ]
            )
        )
