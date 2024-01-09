from django.conf import settings
from django.db import models

from apps.user.models import Group, UserProfile


class UserGroup(models.Model):
    class Meta:
        verbose_name = "사용자 그룹"
        verbose_name_plural = "사용자가 속한 그룹 목록"
        unique_together = (("user_id", "group_id"),)

    user = models.ForeignKey(
        verbose_name="사용자",
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        primary_key=True,
        db_index=True,
    )

    group = models.ForeignKey(
        verbose_name="그룹",
        on_delete=models.CASCADE,
        to="user.Group",
        db_index=True,
    )

    @staticmethod
    def search_by_user(self, user: UserProfile):
        return UserGroup.objects.filter(user=user)

    @staticmethod
    def search_by_group(self, group: Group):  # WARNING: Too many results
        return UserGroup.objects.filter(group=group)
