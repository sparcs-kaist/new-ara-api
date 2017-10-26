from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from apps.session.sparcssso import Client


is_beta = [False, True][int(settings.SSO_IS_BETA)]
sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


def home(request):
    raise NotImplementedError


def user_login(request):
    raise NotImplementedError


@require_http_methods(['GET'])
def login_callback(request):
    raise NotImplementedError


def user_logout(request):
    raise NotImplementedError


@login_required(login_url='/session/login/')
def unregister(request):
    raise NotImplementedError

