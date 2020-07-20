from django.db import models
from django.conf import settings

from django_mysql.models import JSONField

from ara.db.models import MetaDataModel


class UserProfile(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '유저 프로필'
        verbose_name_plural = '유저 프로필 목록'
        unique_together = (
            ('uid', 'deleted_at'),
            ('sid', 'deleted_at'),
            ('nickname', 'past_user', 'deleted_at'),
        )

    uid = models.CharField(
        null=True,
        default=None,
        editable=False,
        max_length=30,
        verbose_name='Sparcs SSO uid',
    )
    sid = models.CharField(
        null=True,
        default=None,
        editable=False,
        max_length=30,
        verbose_name='Sparcs SSO sid',
    )
    sso_user_info = JSONField(
        editable=False,
        verbose_name='Sparcs SSO 정보',
    )

    picture = models.ImageField(
        null=True,
        default=None,
        upload_to='user_profiles/pictures',
        verbose_name='프로필',
    )
    nickname = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name='닉네임',
    )
    see_sexual = models.BooleanField(
        default=False,
        verbose_name='성인/음란성 보기',
    )
    see_social = models.BooleanField(
        default=False,
        verbose_name='정치/사회성 보기',
    )
    extra_preferences = JSONField(
        editable=False,
        verbose_name='기타 설정',
    )

    user = models.OneToOneField(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name='profile',
        verbose_name='사용자',
        primary_key=True,
    )

    past_user = models.BooleanField(
        default=False,
        verbose_name='이전 사용자',
    )

    def __str__(self):
        return self.user.username
