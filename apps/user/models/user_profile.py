import json

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy
from django_mysql.models import JSONField

from ara.db.models import MetaDataModel
from ara.settings import MIN_TIME


class UserProfile(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "유저 프로필"
        verbose_name_plural = "유저 프로필 목록"
        unique_together = (
            ("uid", "deleted_at"),
            ("sid", "deleted_at"),
            ("nickname", "is_newara", "deleted_at"),
        )

    class UserGroup(models.IntegerChoices):
        # 뉴아라 계정을 만들지 않은 사람들
        UNAUTHORIZED = 0, gettext_lazy("Unauthorized user")
        # 카이스트 메일을 가진 사람 (학생, 교직원)
        KAIST_MEMBER = 1, gettext_lazy("KAIST member")
        # 교내 입주 업체 직원
        STORE_EMPLOYEE = 2, gettext_lazy("Store employee")
        # 카이스트 메일이 없는 개인 (특수한 관련자 등)
        OTHER_MEMBER = 3, gettext_lazy("Other member")
        # 교내 학생 단체들
        KAIST_ORG = 4, gettext_lazy("KAIST organization")
        # 외부인 (홍보 계정 등)
        EXTERNAL_ORG = 5, gettext_lazy("External organization")
        # 소통게시판 관리인
        COMMUNICATION_BOARD_ADMIN = 6, gettext_lazy("Communication board admin")
        # 뉴스게시판 관리인
        NEWS_BOARD_ADMIN = 7, gettext_lazy("News board admin")

    OFFICIAL_GROUPS = [UserGroup.STORE_EMPLOYEE, UserGroup.KAIST_ORG]

    uid = models.CharField(
        null=True,
        default=None,
        editable=False,
        max_length=30,
        verbose_name="Sparcs SSO uid",
    )
    sid = models.CharField(
        null=True,
        default=None,
        editable=False,
        max_length=30,
        verbose_name="Sparcs SSO sid",
    )
    sso_user_info = JSONField(
        editable=False,
        verbose_name="Sparcs SSO 정보",
    )
    picture = models.ImageField(
        null=True,
        blank=True,
        default=None,
        upload_to="user_profiles/pictures",
        verbose_name="프로필",
    )
    nickname = models.CharField(
        blank=True,
        default="",
        max_length=128,
        verbose_name="닉네임",
    )
    nickname_updated_at = models.DateTimeField(
        default=MIN_TIME, verbose_name="최근 닉네임 변경일시"
    )
    see_sexual = models.BooleanField(
        default=False,
        verbose_name="성인/음란성 보기",
    )
    see_social = models.BooleanField(
        default=False,
        verbose_name="정치/사회성 보기",
    )
    extra_preferences = JSONField(
        editable=False,
        verbose_name="기타 설정",
    )
    group = models.IntegerField(
        choices=UserGroup.choices, default=UserGroup.UNAUTHORIZED
    )
    user = models.OneToOneField(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="profile",
        verbose_name="사용자",
        primary_key=True,
    )
    # 포탈 공지에서 긁어온 작성자 or 이전한 아라 사용자는 is_newara=False
    is_newara = models.BooleanField(
        default=True,
        verbose_name="뉴아라 사용자",
    )
    ara_id = models.CharField(
        blank=True,
        default="",
        max_length=128,
        verbose_name="이전 아라 아이디",
    )
    agree_terms_of_service_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="약관 동의 일시",
    )
    inactive_due_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="활동정지 마감 일시",
    )

    def __str__(self) -> str:
        return self.nickname

    def can_change_nickname(self) -> bool:
        return (timezone.now() - relativedelta(months=3)) >= self.nickname_updated_at

    @cached_property
    def email(self) -> str:
        return self.user.email

    @cached_property
    def realname(self) -> str:
        sso_info = self.sso_user_info
        user_realname = (
            json.loads(sso_info["kaist_info"])["ku_kname"]
            if sso_info["kaist_info"]
            else sso_info["last_name"] + sso_info["first_name"]
        )

        return user_realname

    @cached_property
    def is_official(self) -> bool:
        return (
            self.group in UserProfile.OFFICIAL_GROUPS
            or self.user.email == "new-ara@sparcs.org"
        )

    @cached_property
    def is_school_admin(self) -> bool:
        return self.group == UserProfile.UserGroup.COMMUNICATION_BOARD_ADMIN
