from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from ara.classes.model import MetaDataModel

from apps.session.sparcssso import Client


is_beta = bool(int(settings.SSO_IS_BETA))

sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


class UserProfile(MetaDataModel):
    # SPARCS SSO spec
    sid = models.CharField(max_length=30)

    signature = models.TextField(
        blank=True,
        verbose_name='서명',
    )
    see_sexual = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='성인/음란성 보기',
    )
    see_social = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='정치/사회성 보기',
    )
    user_nickname = models.CharField(
        blank=True,
        max_length=128,
        verbose_name='닉네임',
    )
    profile_picture = models.ImageField(
        blank=True,
        verbose_name='프로필',
    )

    user = models.OneToOneField(
        to=User,
        related_name='profile',
        verbose_name='사용자',
    )

    def __str__(self):
        return self.user.username
