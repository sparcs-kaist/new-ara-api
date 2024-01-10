from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

if TYPE_CHECKING:
    from apps.user.models import Group, UserProfile


class UserGroup(models.Model):
    class Meta:
        verbose_name = "사용자 그룹"
        verbose_name_plural = "사용자가 속한 그룹 목록"
        unique_together = (("user", "group"),)

    user = models.ForeignKey(
        verbose_name="사용자",
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
    )

    group = models.ForeignKey(
        verbose_name="그룹",
        on_delete=models.CASCADE,
        to="user.Group",
        db_index=True,
    )

    @staticmethod
    def search_by_user(self, user: UserProfile) -> list[Group]:
        groups = []
        for usergroup in UserGroup.objects.filter(user=user):
            groups.append(usergroup.group)
        return groups

    @staticmethod
    def search_by_group(
        self, group: Group
    ) -> list[UserProfile]:  # WARNING: Too many results
        users = []
        for usergroup in UserGroup.objects.filter(group=group):
            users.append(usergroup.user)
        return users
