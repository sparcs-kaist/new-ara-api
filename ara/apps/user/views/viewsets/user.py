from django.contrib.auth import get_user_model

from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.user.permissions.user import UserPermission
from apps.user.serializers.user import (
    UserSerializer,
    UserDetailActionSerializer,
)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    ActionAPIViewSet,
):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    action_serializer_class = {
        'retrieve': UserDetailActionSerializer,
    }
    permission_classes = (
        UserPermission,
    )
