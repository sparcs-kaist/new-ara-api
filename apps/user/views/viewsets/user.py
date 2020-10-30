import uuid
import random
from urllib.parse import urlparse

from cached_property import cached_property
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status, response, decorators, permissions

from apps.user.models.user.manual import ManualUser
from ara.classes.viewset import ActionAPIViewSet
from ara.classes.sparcssso import Client as SSOClient

from apps.user.models import UserProfile
from apps.user.permissions.user import UserPermission


def _make_random_name() -> str:
    nouns = ['외계인', '펭귄', '코뿔소', '여우', '염소', '타조', '사과', '포도', '다람쥐', '도토리', '해바라기', '코끼리', '돌고래', '거북이', '나비', '앵무새', '알파카', '강아지', '고양이', '원숭이', '두더지', '낙타', '망아지', '시조새', '힙스터', '로봇', '감자', '고구마', '가마우지', '직박구리', '오리너구리', '보노보', '개미핥기', '치타', '사자', '구렁이', '도마뱀', '개구리', '올빼미', '부엉이']
    adjectives = ['부지런한', '즐거운', '열렬한', '유쾌한', '환호하는', '소심한', '빛나는', '열정적인', '유연한', '행복한', '활동적인', '용감한', '겸손한', '관대한', '따뜻한', '재미있는', '유능한', '예의바른', '생각하는',  '침착한', '태평한', '꼼꼼한', '정직한', '신중한', '창의적인', '가냘픈', '신나는', '귀여운', '기쁜', '귀찮은', '날랜', '바쁜', '듬직한', '사나운', '똑똑한', '더운', '추운', '징그러운', '젊은', '늙은']
    random.shuffle(nouns)
    random.shuffle(adjectives)
    temp_nickname = adjectives[0] + ' ' + nouns[0]
    try:
        duplicate_user_profile = UserProfile.objects.get(
            nickname=temp_nickname,
        )
        tmparr = str(duplicate_user_profile.nickname).split(' ')
        if len(tmparr) == 3:
            temp_nickname += ' ' + str(int(tmparr[-1]) + 1)
        else:
            temp_nickname += ' 1'
    except UserProfile.DoesNotExist:
        pass
    return temp_nickname


def make_random_profile_picture() -> str:
    colors = ['blue', 'red', 'gray']
    random.shuffle(colors)
    numbers = ['1', '2', '3']
    random.shuffle(numbers)

    temp_color = colors[0]
    temp_num = numbers[0]
    default_picture = f'user_profiles/default_pictures/{temp_color}-default{temp_num}.png'

    return default_picture


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

    @cached_property
    def sso_client(self):
        return SSOClient(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=settings.SSO_IS_BETA)

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
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_info = self.sso_client.get_user_info(request.GET['code'])

        # Bypass SSO validation
        # if not request.GET.get('state'):
        #     return response.Response(
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        #
        # user_info = {
        #     'kaist_id': 'foo',
        #     'sid': request.GET.get('state'),
        #     'uid': request.GET.get('state'),
        #     'email': 'foo@bar.com'
        # }

        is_kaist = user_info.get('kaist_id') is not None

        manual_user = ManualUser.objects.filter(sso_email=user_info['email']).first()
        is_manual = manual_user is not None

        try:  # 로그인
            user_profile = UserProfile.objects.get(
                sid=user_info['sid'],
            )
            user_profile.sso_user_info = user_info

        except UserProfile.DoesNotExist:  # 회원가입
            user_nickname = _make_random_name()
            user_profile_picture = make_random_profile_picture()
            with transaction.atomic():
                new_user = get_user_model().objects.create_user(
                    email=user_info['email'],
                    username=str(uuid.uuid4()),
                    password=str(uuid.uuid4()),
                    is_active=is_kaist or is_manual,
                )
                user_group = UserProfile.UserGroup.UNAUTHORIZED

                if is_manual:
                    manual_user.user = new_user
                    manual_user.save()
                    user_nickname = manual_user.org_name

                    user_group = manual_user.org_type

                elif is_kaist:
                    user_group = UserProfile.UserGroup.KAIST_MEMBER

                user_profile = UserProfile.objects.create(
                    uid=user_info['uid'],
                    sid=user_info['sid'],
                    nickname=user_nickname,
                    sso_user_info=user_info,
                    user=new_user,
                    group=user_group,
                    picture=user_profile_picture,
                )

        if not user_profile.user.is_active:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile.user.last_login = timezone.now()
        user_profile.user.save()

        login(request, user_profile.user)

        _next = request.session.get('next', '/')

        # redirect to frontend's terms of service agreement page if user did not agree it yet
        if request.user.is_authenticated and request.user.profile.agree_terms_of_service_at is None:
            _next = urlparse(_next)
            return redirect(to=f'{_next.scheme}://{_next.netloc}/tos')

        return redirect(to=_next)

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

    @decorators.action(detail=True, methods=['delete'])
    def sso_logout(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)
            # In case of user who isn't logged in with Sparcs SSO
            if not request.user.profile.sid:
                return response.Response(
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return self.sso_client.get_logout_url(
            sid=request.user.profile.sid,
            redirect_uri=request.GET.get('next', 'https://sparcssso.kaist.ac.kr/'),
        )
