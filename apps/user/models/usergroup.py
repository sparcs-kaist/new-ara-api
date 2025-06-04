from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from .group import Group

if TYPE_CHECKING:
    from apps.user.models import UserProfile


class UserGroup(models.Model):
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

    class Meta:
        verbose_name = "사용자 그룹"
        verbose_name_plural = "사용자가 속한 그룹 목록"
        unique_together = (("user", "group"),)

    @staticmethod
    def search_by_user(user: settings.AUTH_USER_MODEL) -> list[Group]:
        return Group.objects.filter(usergroup__user=user).all()

    @staticmethod
    def search_by_group(group: Group) -> list[UserProfile]:  # WARNING: Too many results
        return UserProfile.objects.filter(usergroup__group=group).all()
