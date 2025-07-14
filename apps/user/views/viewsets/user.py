import hashlib
import json
import random
import uuid
from urllib.parse import urlparse

import jwt
import requests
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout
from django.db import transaction
from django.shortcuts import redirect, reverse
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import decorators, permissions, response, status

from apps.user.models import UserProfile
from apps.user.models.user.manual import ManualUser
from apps.user.permissions.user import UserPermission
from ara.classes.sparcssso import Client as SSOClient
from ara.classes.viewset import ActionAPIViewSet

#for jwt
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse

#for log
import logging
logger = logging.getLogger("auth_logger")

NOUNS = [
    "외계인",
    "펭귄",
    "코뿔소",
    "여우",
    "염소",
    "타조",
    "사과",
    "포도",
    "다람쥐",
    "도토리",
    "해바라기",
    "코끼리",
    "돌고래",
    "거북이",
    "나비",
    "앵무새",
    "알파카",
    "강아지",
    "고양이",
    "원숭이",
    "두더지",
    "낙타",
    "망아지",
    "시조새",
    "힙스터",
    "로봇",
    "감자",
    "고구마",
    "가마우지",
    "직박구리",
    "오리너구리",
    "보노보",
    "개미핥기",
    "치타",
    "사자",
    "구렁이",
    "도마뱀",
    "개구리",
    "올빼미",
    "부엉이",
]
ADJECTIVES = [
    "부지런한",
    "즐거운",
    "열렬한",
    "유쾌한",
    "환호하는",
    "소심한",
    "빛나는",
    "열정적인",
    "유연한",
    "행복한",
    "활동적인",
    "용감한",
    "겸손한",
    "관대한",
    "따뜻한",
    "재미있는",
    "유능한",
    "예의바른",
    "생각하는",
    "침착한",
    "태평한",
    "꼼꼼한",
    "정직한",
    "신중한",
    "창의적인",
    "가냘픈",
    "신나는",
    "귀여운",
    "기쁜",
    "귀찮은",
    "날랜",
    "바쁜",
    "듬직한",
    "사나운",
    "똑똑한",
    "더운",
    "추운",
    "징그러운",
    "젊은",
    "늙은",
]


def _make_random_name() -> str:
    random.shuffle(NOUNS)
    random.shuffle(ADJECTIVES)
    temp_nickname = ADJECTIVES[0] + " " + NOUNS[0]
    try:
        UserProfile.objects.get(nickname=temp_nickname)
        random_value = str(timezone.datetime.now().timestamp())
        sha1 = hashlib.sha256()
        sha1.update(bytes(random_value, "utf-8"))
        sha1.update(bytes(temp_nickname, "utf-8"))
        temp_nickname += "_" + sha1.hexdigest()[:4]

    except UserProfile.DoesNotExist:
        pass
    return temp_nickname


def get_profile_picture(hash_val=None) -> str:
    colors = ["blue", "red", "gray"]
    numbers = ["1", "2", "3"]

    if hash_val is None:
        col = random.choice(colors)
        num = random.choice(numbers)
    else:
        nidx, cidx = divmod(hash_val, len(colors))
        col = colors[cidx]
        num = numbers[nidx % len(numbers)]

    return f"user_profiles/default_pictures/{col}-default{num}.png"


class UserViewSet(ActionAPIViewSet):
    queryset = get_user_model().objects.all()
    permission_classes = (UserPermission,)
    action_permission_classes = {
        "sso_login": (permissions.AllowAny,),
        "sso_login_callback": (permissions.AllowAny,),
        "refresh_token": (permissions.AllowAny,),
    }

    @cached_property
    def sso_client(self):
        return SSOClient(
            settings.SSO_CLIENT_ID,
            settings.SSO_SECRET_KEY,
            is_beta=settings.SSO_IS_BETA,
        )

    @decorators.action(detail=False, methods=["get"])
    def sso_login(self, request, *args, **kwargs):
        request.session["next"] = request.GET.get("next", "/")

        sso_login_url, request.session["state"] = self.sso_client.get_login_params()

        return redirect(
            to=sso_login_url,
        )

    @decorators.action(detail=False, methods=["get"])
    def sso_login_callback(self, request, *args, **kwargs):
        if not request.GET.get("code") or not request.GET.get("state"):
            return response.Response(
                status=status.HTTP_400_BAD_REQUEST,
            )

        # logging
        logger.info(
            f" Requested state: {request.GET.get('state')}, Session state: {request.session.get('state')}"
        )

        # Security Issues
        if request.GET.get("state") != request.session.get("state"):
            return response.Response(
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user_info = self.sso_client.get_user_info(request.GET["code"])

        except requests.exceptions.HTTPError as http_error:
            try:
                code = json.loads(http_error.response.content)["code"]

            except:
                code = "json-loads-error"

            return redirect(
                to=reverse("core:InvalidSsoLoginView")
                + f"?code={code}&status_code={http_error.response.status_code}"
            )

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

        is_kaist = (user_info.get("kaist_id") is not None) or (
            user_info.get("email").split("@")[-1] == "kaist.ac.kr"
        )

        manual_user = ManualUser.objects.filter(sso_email=user_info["email"]).first()
        is_manual = manual_user is not None

        try:  # 로그인
            user_profile = UserProfile.objects.get(
                uid=user_info["uid"],
            )

            if user_profile.inactive_due_at:
                if timezone.now() < user_profile.inactive_due_at:
                    return response.Response(
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    user_profile.inactive_due_at = None
                    user_profile.user.is_active = True

            user_profile.sso_user_info = user_info
            user_profile.save()

            # 1. 카이포탈 인증 이전, 회원가입을 시도했던 회원 (나중에 카이포탈 인증 후 다시 로그인 시도)
            # 2. 아직 승인 이전, 회원가입을 시도했던 공용 계정 회원
            if (not user_profile.user.is_active) and (is_kaist or is_manual):
                user_profile.user.is_active = True
                if is_manual:
                    user_profile.group = manual_user.org_type
                elif is_kaist:
                    user_profile.group = UserProfile.UserGroup.KAIST_MEMBER
                    user_profile.sso_user_info = user_info
                user_profile.save()

        except UserProfile.DoesNotExist:  # 회원가입
            user_nickname = _make_random_name()
            user_profile_picture = get_profile_picture()
            email = user_info["email"]

            if email.split("@")[-1] == "sso.sparcs.org":  # sso에서 random하게 만든 이메일인 경우
                kaist_info = user_info["kaist_info"]
                if kaist_info:  # SNS 회원가입 후 카이생 인증
                    kaist_info = json.loads(kaist_info)
                    kaist_email = kaist_info["mail"]
                    email = kaist_email

            with transaction.atomic():
                new_user = get_user_model().objects.create_user(
                    email=email,
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
                    uid=user_info["uid"],
                    sid=user_info["sid"],
                    nickname=user_nickname,
                    sso_user_info=user_info,
                    user=new_user,
                    group=user_group,
                    picture=user_profile_picture,
                )

        if not user_profile.user.is_active:
            return redirect(
                to=reverse("core:InvalidSsoLoginView")
                + f"?code=not-kaist-and-not-manual&status_code=400"
            )

        user_profile.user.last_login = timezone.now()
        user_profile.user.save()

        login(request, user_profile.user)

        #jwt token
        refresh = RefreshToken.for_user(user_profile.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        _next = request.session.get("next", "/")

        # 이용약관 미동의자
        if (request.user.is_authenticated and
            request.user.profile.agree_terms_of_service_at is None):
            tos_url = f"{urlparse(_next).scheme}://{urlparse(_next).netloc}/tos"
        else:
            tos_url = None

        # API 요청이면 JSON 응답, 아니면 redirect
        if request.headers.get("Accept") == "application/json" or request.GET.get("mode") == "json":
            res = JsonResponse({
                "detail": "login success",
                "next": tos_url or _next,
                "access": access_token,
                "refresh": refresh_token,
            })
            res.set_cookie("access", access_token) #프로덕션 환경에서는 보안 설정 필요.
            res.set_cookie("refresh", refresh_token)
            return res

        # 웹 요청이면 기존 redirect 흐름 유지
        res = redirect(to=tos_url or _next)
        res.set_cookie("access", access_token)
        res.set_cookie("refresh", refresh_token)
        return res

    @decorators.action(detail=True, methods=["post"])
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

    @decorators.action(detail=True, methods=["delete"])
    def sso_logout(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logout(request)

        return response.Response(
            status=status.HTTP_200_OK,
        )

    #jwt -> refresh toekn
    @decorators.action(detail=False, methods=['post'])
    def refresh_token(self, request):
        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            return response.Response({'error': 'Refresh token not provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)
        except Exception:
            return response.Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)

        resp = response.Response({'access': access_token})
        resp.set_cookie(
            'access',
            access_token,
            httponly=True,
            secure=True,
            samesite='Lax',
        )
        return resp

    @decorators.action(detail=False, methods=["post"], url_path="oneapp-login", permission_classes=[permissions.AllowAny],authentication_classes=[])
    def oneapp_login(self, request):
        """ 
        One App JWT Access Token 기반 간편 로그인/회원가입
        """
        import datetime

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return response.Response({"error": "No JWT token"}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, settings.ONE_APP_JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return response.Response({
                "error": f"Expired JWT token"
            }, status=status.HTTP_401_UNAUTHORIZED)

        except jwt.DecodeError:
            return response.Response({
                "error": f"Decode error in JWT token"
            }, status=status.HTTP_401_UNAUTHORIZED)

        except jwt.InvalidTokenError:
            return response.Response({
                "error": f"Invalid JWT token"
            }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return response.Response({
                "error": f"Unexpected error during JWT decode: {type(e).__name__}: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        uid = payload.get("uid")
        oid = payload.get("oid")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d")

        # POST payload에서 kaist info 정보 가져오기
        # POST payload 전체가 kaist_v2_info임.
        post_data = request.data

        # user_info 빌드
        user_info = {
            "sid": None,
            "uid": uid,
            "email": post_data.get("email"),
            "flags": [],
            "gender": "",
            "birthday": "",
            "kaist_id": post_data.get("ku_std_no") or post_data.get("kaist_uid"),
            "last_name": post_data.get("user_eng_nm", "").split(",")[0].strip(),
            "sparcs_id": None,
            "first_name": post_data.get("user_eng_nm", "").split(",")[1].strip(),
            "kaist_info": None,
            "twitter_id": None,
            "facebook_id": None,
            "kaist_v2_info": post_data,
            "kaist_info_time": "",
            "kaist_v2_info_time": now_str,
        }

        # UserProfile 생성/조회
        from django.contrib.auth import get_user_model
        try:
            profile = UserProfile.objects.get(uid=uid)
            user = profile.user
        except UserProfile.DoesNotExist:  # 회원가입
            user_nickname = _make_random_name()
            user_profile_picture = get_profile_picture()
            email = user_info["email"]

            with transaction.atomic():
                new_user = get_user_model().objects.create_user(
                    email=email,
                    username=str(uuid.uuid4()),
                    password=str(uuid.uuid4()),
                    is_active=True #One App 로그인 -> 항상 활성화된 상태
                )
                user_group = UserProfile.UserGroup.KAIST_MEMBER

                user_profile = UserProfile.objects.create(
                    uid=uid,
                    sid=None, #One App -> sid 저장하지 않음.
                    nickname=user_nickname,
                    sso_user_info=user_info,
                    user=new_user,
                    group=user_group,
                    picture=user_profile_picture,
                )

        return response.Response({
            "detail": "oneapp login success",
            "uid": uid,
            "nickname": user_profile.nickname if 'user_profile' in locals() else profile.nickname,
            "oid": oid,
            "user_info": user_info,
            "user_id": (user_profile.user.id if 'user_profile' in locals() else user.id),
        }, status=status.HTTP_200_OK)
