from rest_framework import decorators, response, serializers, status, viewsets

from apps.core.filters.notification import NotificationFilter
from apps.core.models import Notification, NotificationReadLog
from apps.core.serializers.notification import NotificationSerializer
from ara.classes.viewset import ActionAPIViewSet


class NotificationViewSet(viewsets.ReadOnlyModelViewSet, ActionAPIViewSet):
    queryset = Notification.objects.all()
    filterset_class = NotificationFilter
    serializer_class = NotificationSerializer
    action_serializer_class = {
        "read": serializers.Serializer,
        "read_all": serializers.Serializer,
    }

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Notification.objects.none()

        queryset = super().get_queryset()

        queryset = (
            queryset.filter(
                notification_read_log_set__read_by=self.request.user,
            )
            .select_related(
                "related_article",
                "related_comment",
                "related_chat_room",
            )
            .prefetch_related(
                "related_article__attachments",
                NotificationReadLog.prefetch_my_notification_read_log(
                    self.request.user
                ),
            )
        )

        return queryset

    @decorators.action(detail=False, methods=["post"])
    def read_all(self, request, *args, **kwargs):
        notification_read_logs = NotificationReadLog.objects.filter(
            read_by=request.user,
            notification__in=[notification.id for notification in self.get_queryset()],
        )

        notification_read_logs.update(is_read=True)

        return response.Response(
            status=status.HTTP_200_OK,
        )

    @decorators.action(detail=True, methods=["post"])
    def read(self, request, *args, **kwargs):
        try:
            notification_read_log = self.get_object().notification_read_log_set.get(
                read_by=request.user,
            )

            notification_read_log.is_read = True

            notification_read_log.save()

        except NotificationReadLog.DoesNotExist:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response.Response(
            status=status.HTTP_200_OK,
        )
