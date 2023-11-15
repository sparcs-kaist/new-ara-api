from rest_framework import viewsets

from apps.calendar.models import Calendar, Tag
from apps.calendar.serializers.calendar import CalendarSerializer, TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class CalendarViewSet(viewsets.ModelViewSet):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
