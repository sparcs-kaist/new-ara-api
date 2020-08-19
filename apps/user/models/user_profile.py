import datetime
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

from django_mysql.models import JSONField

from ara.db.models import MetaDataModel


class UserProfile(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '유저 프로필'
        verbose_name_plural = '유저 프로필 목록'
        unique_together = (
            ('uid', 'deleted_at'),
            ('sid', 'deleted_at'),
            ('nickname', 'is_newara', 'deleted_at'),
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
    nickname_updated_at = models.DateTimeField(
        default=datetime.datetime.min,
        verbose_name='최근 닉네임 변경일시'
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

    is_kaist = models.BooleanField(
        default=False,
        verbose_name='카이스트 인증된 사용자'
    )

    # 포탈 공지에서 긁어온 작성자 or 이전한 아라 사용자는 is_newara=False
    is_newara = models.BooleanField(
        default=True,
        verbose_name='뉴아라 사용자',
    )

    ara_id = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name='이전 아라 아이디',
    )

    def __str__(self):
        return self.user.username

    def can_change_nickname(self) -> bool:
        return (timezone.now() - relativedelta(months=3)) >= self.nickname_updated_at
