import json

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy

from apps.user.models import Group
from ara.db.models import MetaDataModel
from ara.settings import MIN_TIME

from .usergroup import UserGroup


class UserProfile(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "유저 프로필"
        verbose_name_plural = "유저 프로필 목록"
        unique_together = (
            ("uid", "deleted_at"),
            ("sid", "deleted_at"),
            ("nickname", "is_newara", "deleted_at"),
        )

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
    sso_user_info = models.JSONField(
        default=dict,
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
        default=MIN_TIME,
        verbose_name="최근 닉네임 변경일시",
    )
    see_sexual = models.BooleanField(
        default=False,
        verbose_name="성인/음란성 보기",
    )
    see_social = models.BooleanField(
        default=False,
        verbose_name="정치/사회성 보기",
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

    @staticmethod
    def get_by_auth_user(user: settings.AUTH_USER_MODEL) -> "UserProfile":
        return UserProfile.objects.get(user=user)

    @cached_property
    def email(self) -> str:
        return self.user.email

    @cached_property
    def realname(self) -> str:
        if not self.sso_user_info:
            return self.nickname  # Portal crawled users

        kaist_info = self.sso_user_info["kaist_info"]
        if kaist_info:
            return json.loads(kaist_info)["ku_kname"]
        return self.sso_user_info["last_name"] + self.sso_user_info["first_name"]

    @cached_property
    def is_official(self) -> bool:
        if self.user.email == "new-ara@sparcs.org":
            return True
        return any(group.is_official for group in self.groups)

    @cached_property
    def is_school_admin(self) -> bool:
        return self.has_group_by_id(7)  # 7 = Communication board admin

    @cached_property
    def groups(self) -> list[Group]:
        return UserGroup.search_by_user(self.user)

    def has_group(self, group: Group) -> bool:
        return group in self.groups

    def has_group_by_name(self, group_name: str) -> bool:
        return any(group.name == group_name for group in self.groups)

    def has_group_by_id(self, group_id: int) -> bool:
        return any(group.group_id == group_id for group in self.groups)

    def add_group(self, group: Group) -> None:
        UserGroup.objects.get_or_create(user=self.user, group=group)

    def add_group_by_id(self, group_id: int) -> None:
        group = Group.search_by_id(group_id)
        self.add_group(group)

    def remove_group(self, group: Group) -> None:
        if self.has_group(group):
            UserGroup.objects.get(user=self.user, group=group).delete()

    def remove_group_by_id(self, group_id: int) -> None:
        group = Group.search_by_id(group_id)
        self.remove_group(group)
