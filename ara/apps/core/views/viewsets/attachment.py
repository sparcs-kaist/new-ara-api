from django.http import HttpResponseRedirect

from rest_framework import mixins, decorators

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Attachment
from apps.core.serializers.attachment import AttachmentSerializer
from apps.core.permissions.attachment import AttachmentPermission


class AttachmentViewSet(mixins.CreateModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.DestroyModelMixin,
                        ActionAPIViewSet):
    queryset = Attachment.objects.all()
    permission_classes = (
        AttachmentPermission,
    )
    serializer_class = AttachmentSerializer

    @decorators.detail_route(methods=['get'])
    def url(self, request, *args, **kwargs):
        return HttpResponseRedirect(
            redirect_to=self.get_object().file.url,
        )
