from rest_framework import viewsets

from apps.global_notice.models import GlobalNotice
from apps.global_notice.serializers import GlobalNoticeSerializer


class GlobalNoticeViewSet(viewsets.ModelViewSet):
    queryset = GlobalNotice.objects.all()
    serializer_class = GlobalNoticeSerializer
