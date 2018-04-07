from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Attachment
from apps.core.serializers.attachment import AttachmentSerializer
from apps.core.permissions.attachment import AttachmentPermission


class AttachmentViewSet(mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        ActionAPIViewSet):
    queryset = Attachment.objects.all()
    permission_classes = (
        AttachmentPermission,
    )
    serializer_class = AttachmentSerializer
