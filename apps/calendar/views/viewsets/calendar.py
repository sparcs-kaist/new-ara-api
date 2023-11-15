from apps.calendar.models import Calendar
from apps.calendar.serializers.calendar import CalendarSerializer
from apps.user.permissions.user_profile import UserProfilePermission
from apps.user.serializers.user_profile import (
    PublicUserProfileSerializer,
    UserProfileUpdateActionSerializer,
)
from ara.classes.viewset import ActionAPIViewSet


class CalendarViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, ActionAPIViewSet
):
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer
    action_serializer_class = {
        "update": UserProfileUpdateActionSerializer,
        "partial_update": UserProfileUpdateActionSerializer,
    }
    permission_classes = (UserProfilePermission,)

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        if request.user == profile.user:
            return super().retrieve(request, *args, **kwargs)
        else:
            return response.Response(PublicUserProfileSerializer(profile).data)

    def list(self, request):
        queryset = User.objects.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = User.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)
