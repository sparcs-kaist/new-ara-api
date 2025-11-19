from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from meal.models import CafeteriaMenu
from meal.serializers import CafeteriaMenuSerializer

class CafeteriaMenuViewSet(viewsets.ModelViewSet):
    queryset = CafeteriaMenu.objects.all()
    serializer_class = CafeteriaMenuSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["date", "meal_time"]
    ordering_fields = ["date", "meal_time"]
