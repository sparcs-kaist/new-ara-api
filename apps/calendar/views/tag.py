from rest_framework import viewsets

from apps.calendar.models import Tag
from apps.calendar.serializers.tag import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
