from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Attachment
from apps.core.serializers.attachment import AttachmentSerializer


class AttachmentViewSet(mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        ActionAPIViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
