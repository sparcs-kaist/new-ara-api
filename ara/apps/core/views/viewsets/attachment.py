from rest_framework import viewsets

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Attachment
from apps.core.serializers.attachment import AttachmentSerializer


class AttachmentViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
