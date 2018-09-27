from django.shortcuts import redirect

from rest_framework import mixins, decorators, permissions

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Attachment
from apps.core.serializers.attachment import AttachmentSerializer
from apps.core.permissions.attachment import AttachmentPermission


class AttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (
        AttachmentPermission,
    )
    action_permission_classes = {
        'url': (
            permissions.AllowAny,
        ),
    }

    def perform_create(self, serializer):
        serializer.save(
            name=self.request.FILES['file'].name,
        )

    @decorators.detail_route(methods=['get'])
    def url(self, request, *args, **kwargs):
        return redirect(
            to=self.get_object().file.url,
        )
