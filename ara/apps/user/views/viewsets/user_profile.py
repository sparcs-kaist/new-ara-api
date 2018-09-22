from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.user.models import UserProfile
from apps.user.permissions.user_profile import UserProfilePermission
from apps.user.serializers.user_profile import (
    UserProfileSerializer,
    UserProfileUpdateActionSerializer,
)


class UserProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    ActionAPIViewSet,
):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    action_serializer_class = {
        'update': UserProfileUpdateActionSerializer,
    }
    permission_classes = (
        UserProfilePermission,
    )
