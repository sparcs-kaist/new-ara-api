from rest_framework import viewsets

from apps.calendar.models import Event
from apps.calendar.serializers.event import EventSerializer


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
