from django.shortcuts import redirect
from rest_framework import decorators, mixins, permissions

from apps.core.models import Attachment
from apps.core.permissions.attachment import AttachmentPermission
from apps.core.serializers.attachment import AttachmentSerializer
from ara.classes.viewset import ActionAPIViewSet


class AttachmentViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (AttachmentPermission,)
    action_permission_classes = {
        "url": (permissions.AllowAny,),
    }

    def perform_create(self, serializer):
        serializer.save(
            size=self.request.FILES["file"].size,
            mimetype=self.request.FILES["file"].content_type,
        )

    @decorators.action(detail=True, methods=["get"])
    def url(self, request, *args, **kwargs):
        return redirect(
            to=self.get_object().file.url,
        )
