from django.utils import timezone
from rest_framework import permissions, viewsets

from apps.global_notice.models import GlobalNotice
from apps.global_notice.permissions import (
    GlobalNoticePermission,
    IsGlobalNoticeAthenticated,
)
from apps.global_notice.serializers import GlobalNoticeSerializer


class GlobalNoticeViewSet(viewsets.ModelViewSet):
    queryset = GlobalNotice.objects.filter(
        started_at__lte=timezone.now(), expired_at__gte=timezone.now()
    )
    serializer_class = GlobalNoticeSerializer

    permission_classes = (
        IsGlobalNoticeAthenticated,
        GlobalNoticePermission,
    )
    action_permission_classes = {
        "create": (permissions.IsAuthenticated, GlobalNoticePermission)
    }
    pagination_class = None
