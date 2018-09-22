from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

from rest_framework import mixins, decorators, permissions
from rest_framework_jwt.settings import api_settings

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
    action_permission_classes = {
        'login': (
            permissions.AllowAny,
        ),
    }

    @property
    def sso_client(self):
        return SSOClient(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=settings.SSO_IS_BETA)

    @staticmethod
    def get_jwt(user):
        return api_settings.JWT_ENCODE_HANDLER(
            payload=api_settings.JWT_PAYLOAD_HANDLER(
                user=user,
            )
        )

    @decorators.list_route(methods=['get'])
    def login(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next', '/')

        sso_login_url, request.session['sso_state'] = self.sso_client.get_login_params()

        return redirect(sso_login_url)
