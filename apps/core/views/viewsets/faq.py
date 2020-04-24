from rest_framework import viewsets, permissions

from apps.core.serializers.faq import FAQSerializer
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import FAQ


class FAQViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
