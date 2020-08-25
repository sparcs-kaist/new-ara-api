import uuid
import datetime
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import redirect

from rest_framework import status, response, decorators, permissions
from rest_framework.authtoken.models import Token

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

    #TODO
    @staticmethod
    def get_token(user):
        return Token.objects.get_or_create(user=user)[0]

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
            nouns = ['외계인', '펭귄', '코뿔소', '여우', '염소', '타조', '사과', '포도', '다람쥐', '도토리', '해바라기', '코끼리', '돌고래', '거북이', '나비', '앵무새', '알파카', '강아지', '고양이', '원숭이', '두더지', '낙타', '망아지', '시조새', '힙스터', '로봇', '감자', '고구마', '가마우지', '직박구리', '오리너구리', '보노보', '개미핥기', '치타', '사자', '구렁이', '도마뱀', '개구리', '올빼미', '부엉이']
            adjectives = ['부지런한', '즐거운', '열렬한', '유쾌한', '환호하는', '소심한', '빛나는', '열정적인', '유연한', '행복한', '활동적인', '용감한', '겸손한', '관대한', '따뜻한', '재미있는', '유능한', '예의바른', '생각하는',  '침착한', '태평한', '꼼꼼한', '정직한', '신중한', '창의적인', '가냘픈', '신나는', '귀여운', '기쁜', '귀찮은', '날랜', '바쁜', '듬직한', '사나운', '똑똑한', '더운', '추운', '징그러운', '젊은', '늙은']
            random.shuffle(nouns)
            random.shuffle(adjectives)
            temp_nickname = adjectives[0] + ' ' + nouns[0]

            colors = ["blue", "red", "gray"]
            random.shuffle(colors)
            numbers = ["1", "2", "3"]
            random.shuffle(numbers)

            temp_color = colors[0]
            temp_num = numbers[0]
            default_picture = f"user_profiles/default_pictures/{temp_color}-default{temp_num}.pngitg"

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

            with transaction.atomic():
                user_profile = UserProfile.objects.create(
                    uid=user_info['uid'],
                    sid=user_info['sid'],
                    nickname=temp_nickname,
                    is_kaist=True if user_info.get('kaist_id') else False,
                    sso_user_info=user_info,
                    picture=default_picture,
                    user=get_user_model().objects.create_user(
                        email=user_info['email'],
                        username=str(uuid.uuid4()),
                        password=str(uuid.uuid4()),
                        is_active=True if user_info.get('kaist_id') else False,
                    ),
                )

        if not user_profile.user.is_active:
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_profile.user.last_login = datetime.datetime.now()

        return redirect(
            to='{next}?token={token}'.format(
                next=request.session.pop('next', '/'),
                token=self.get_token(user_profile.user),
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
