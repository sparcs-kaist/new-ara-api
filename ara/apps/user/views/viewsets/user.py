from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from rest_framework import mixins, decorators

from ara.classes.viewset import ActionAPIViewSet
from ara.classes.sparcssso import Client as SSOClient

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

    @property
    def sso_client(self):
        return SSOClient(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=settings.SSO_IS_BETA)
