from cached_property import cached_property
from dateutil.relativedelta import relativedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy
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

    class UserGroup(models.IntegerChoices):
        UNAUTHORIZED = 0, ugettext_lazy('Unauthorized user')
        KAIST_MEMBER = 1, ugettext_lazy('KAIST member')
        FOOD_EMPLOYEE = 2, ugettext_lazy('Restaurant employee')
        OTHER_EMPLOYEE = 3, ugettext_lazy('Other employee')

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
        blank=True,
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
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
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

    group = models.IntegerField(
        choices=UserGroup.choices,
        default=UserGroup.UNAUTHORIZED
    )

    user = models.OneToOneField(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name='profile',
        verbose_name='사용자',
        primary_key=True,
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

    agree_terms_of_service_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='약관 동의 일시',
    )

    inactive_due_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='활동정지 마감 일시',
    )

    is_official = models.BooleanField(
        default=False,
        verbose_name='공식 계정',
    )
    
    is_school_admin = models.BooleanField(
        default=False,
        verbose_name='학교 관리자',
    )

    def __str__(self) -> str:
        return self.nickname

    def can_change_nickname(self) -> bool:
        return (timezone.now() - relativedelta(months=3)) >= self.nickname_updated_at

    @cached_property
    def email(self) -> str:
        return self.user.email

