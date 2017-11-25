from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from rest_framework_jwt.settings import api_settings

from apps.session.sparcssso import Client
from apps.session.models import UserProfile

import random


is_beta = [False, True][int(settings.SSO_IS_BETA)]
sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


def user_login(request):
    user = request.user
    if user and user.is_authenticated():
        return redirect(request.GET.get('next', '/'))

    request.session['next'] = request.GET.get('next', '/')
    login_url, state = sso_client.get_login_params()
    request.session['sso_state'] = state

    return HttpResponseRedirect(login_url)


@require_http_methods(['GET'])
def login_callback(request):
    next_path = request.session.pop('next', '/')
    state_before = request.session.get('sso_state')
    state = request.GET.get('state')

    # Possibility of Session Hijacked
    if state_before != state:
        return JsonResponse(status=403,
                data={
                    'msg': 'TOKEN MISMATCH: session might be hijacked!'
                })

    code = request.GET.get('code')
    user_data = sso_client.get_user_info(code)

    sid = user_data['sid']
    user_list = User.objects.filter(username=sid)
    if not user_list:
        user = User.objects.create_user(
                    username=sid,
                    email=user_data['email'],
                    password=str(random.getrandbits(32)),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
        user.save()

        profile, created = UserProfile.objects.get_or_create(
            sid=sid,
            user=user
        )
        
    else:
        user = authenticate(username=user_list[0].username)
        user = user_list[0]
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.save()
        user_profile = UserProfile.objects.get(user=user)
        user_profile.save()

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    next_path = '{0}?jwt={1}'.format(next_path, api_settings.JWT_ENCODE_HANDLER(
        api_settings.JWT_PAYLOAD_HANDLER(
            request.user
        )
    ))

    return redirect(next_path)


def user_logout(request):
    user = request.user
    if user and user.is_authenticated():
        sid = UserProfile.objects.get(user=user).sid
        redirect_url = request.GET.get('next', request.build_absolute_uri('/'))
        logout_url = sso_client.get_logout_url(sid, redirect_url)
        logout(request)
        return redirect(logout_url)

    else:
        return JsonResponse(status=403,
                data={'msg': 'Should login first'})


@login_required(login_url='/session/login/')
def unregister(request):
    if request.method != 'POST':
        return JsonResponse(status=405,
                data={'msg': 'Should use POST'})

    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    sid = user_profile.sid
    if sso_client.unregister(sid):
        user_profile.delete()
        user.delete()
        logout(request)
        return JsonResponse(status=200, data={})
    else:
        return JsonResponse(status=403,
                data={'msg': 'Unregistered user'})


def login_test(request):
    return JsonResponse(status=200, data={'msg': 'worked'})

