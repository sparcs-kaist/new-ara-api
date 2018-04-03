from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from apps.session.sparcssso import Client


is_beta = [False, True][int(settings.SSO_IS_BETA)]
sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        related_name='profile',
        verbose_name='사용자',
    )

    # SPARCS SSO spec
    sid = models.CharField(max_length=30)

    signature = models.TextField(
        verbose_name='서명',
        blank=True,
    )
    see_sexual = models.BooleanField(
        default=False,
        verbose_name='성인/음란성 보기',
        blank=True,
    )
    see_social = models.BooleanField(
        default=False,
        verbose_name='정치/사회성 보기',
        blank=True,
    )
    user_nickname = models.CharField(
        max_length=128,
        verbose_name='닉네임',
        blank=True,
    )
    profile_picture = models.ImageField(
        verbose_name='프로필',
        blank=True,
    )

    def __str__(self):
        return self.user.username
