from django.db import connections
from django.db.utils import OperationalError
from rest_framework import response, views


class StatusView(views.APIView):
    def get(self, request):
        try:
            c = connections["default"].cursor()
            return response.Response(status=200, headers={"cache-control": "no-cache"})
        except OperationalError:
            return response.Response(status=500, headers={"cache-control": "no-cache"})
