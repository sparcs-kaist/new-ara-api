from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Report
from apps.core.permissions.report import ReportPermission
from apps.core.serializers.report import ReportSerializer, ReportCreateActionSerializer


class ReportViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, ActionAPIViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    action_serializer_class = {
        'create': ReportCreateActionSerializer,
    }
    permission_classes = (
        ReportPermission,
    )

    def get_queryset(self):
        queryset = super(ReportViewSet, self).get_queryset()

        queryset = queryset.filter(
            reported_by=self.request.user,
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            reported_by=self.request.user,
        )
