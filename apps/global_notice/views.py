from django.utils import timezone
from rest_framework import viewsets

from .models import GlobalNotice
from .serializers import GlobalNoticeSerializer


class GlobalNoticeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GlobalNotice.objects.filter(
        started_at__lte=timezone.now(),
        expired_at__gte=timezone.now(),
    )
    serializer_class = GlobalNoticeSerializer
    pagination_class = None
