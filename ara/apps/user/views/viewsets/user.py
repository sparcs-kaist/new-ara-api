import uuid
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect

from rest_framework import status, response, decorators, permissions
from rest_framework_jwt.settings import api_settings

from ara.classes.viewset import ActionAPIViewSet
from ara.classes.sparcssso import Client as SSOClient

from apps.user.models import UserProfile
from apps.user.permissions.user import UserPermission


class UserViewSet(ActionAPIViewSet):
    queryset = get_user_model().objects.all()
    permission_classes = (
        UserPermission,
    )
    action_permission_classes = {
        'sso_login': (
            permissions.AllowAny,
        ),
        'sso_login_callback': (
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

    @decorators.action(detail=False, methods=['get'])
    def sso_login(self, request, *args, **kwargs):
        request.session['next'] = request.GET.get('next', '/')

        sso_login_url, request.session['state'] = self.sso_client.get_login_params()

        return redirect(
            to=sso_login_url,
        )

    @decorators.action(detail=False, methods=['get'])
    def sso_login_callback(self, request, *args, **kwargs):
        if not request.GET.get('code') or not request.GET.get('state'):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Security Issues
        if request.GET.get('state') != request.session.get('state'):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_info = self.sso_client.get_user_info(request.GET['code'])

        try:
            user_profile = UserProfile.objects.get(
                sid=user_info['sid'],
            )

        except UserProfile.DoesNotExist:
            with transaction.atomic():
                user_profile = UserProfile.objects.create(
                    uid=user_info['uid'],
                    sid=user_info['sid'],
                    nickname=str(uuid.uuid4()),
                    sso_user_info=user_info,
                    user=get_user_model().objects.create_user(
                        email=user_info['email'],
                        username=str(uuid.uuid4()),
                        password=str(uuid.uuid4()),
                    ),
                )

        if not user_profile.user.is_active:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile.user.last_login = datetime.datetime.now()

        return redirect(
            to='{next}?jwt={token}'.format(
                next=request.session.pop('next', '/'),
                token=self.get_jwt(user_profile.user),
            ),
        )

    @decorators.action(detail=True, methods=['post'])
    def sso_unregister(self, request, *args, **kwargs):
        # In case of user who isn't logged in with Sparcs SSO
        if not request.user.profile.sid:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not self.sso_client.unregister(request.user.profile.sid):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.is_active = False
        request.user.save()

        return response.Response(
            status=status.HTTP_200_OK,
        )

    @decorators.action(detail=True, methods=['get'])
    def sso_logout_url(self, request, *args, **kwargs):
        # In case of user who isn't logged in with Sparcs SSO
        if not request.user.profile.sid:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.sso_client.get_logout_url(
            sid=request.user.profile.sid,
            redirect_uri=request.GET.get('next', 'https://sparcssso.kaist.ac.kr/'),
        )
