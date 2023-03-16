from rest_framework import permissions, viewsets

from apps.core.models import FAQ
from apps.core.serializers.faq import FAQSerializer
from ara.classes.viewset import ActionAPIViewSet


class FAQViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    permission_classes = (permissions.IsAuthenticated,)
