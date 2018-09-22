import uuid

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_http_methods


from ara.classes.sparcssso import Client

from apps.user.models import UserProfile, OldAraUser

import random

is_beta = [False, True][int(settings.SSO_IS_BETA)]
sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


@csrf_exempt
@require_http_methods(['POST'])
def old_ara_login(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

    old_ara_user = OldAraUser.objects.filter(username=username).first()

    if not old_ara_user or not old_ara_user.compare_password(password):
        return JsonResponse(status=401, data={'success': False})

    return JsonResponse(status=200, data={'success': True})
