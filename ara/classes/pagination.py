from collections import OrderedDict

from rest_framework import pagination, response


class PageNumberPagination(pagination.PageNumberPagination):
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        if self.page is None:
            return response.Response(data)
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
