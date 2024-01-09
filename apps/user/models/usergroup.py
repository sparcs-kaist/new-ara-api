from django.conf import settings
from django.db import models


class UserGroup(models.Model):
    class Meta:
        verbose_name = "사용자 그룹"
        verbose_name_plural = "사용자가 속한 그룹 목록"
        unique_together = (("user_id", "group_id"),)

    user_id = models.ForeignKey(
        verbose_name="사용자",
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        primary_key=True,
        db_index=True,
    )

    group_id = models.ForeignKey(
        verbose_name="그룹",
        on_delete=models.CASCADE,
        to="user.Group",
        db_index=True,
    )

    @staticmethod
    def search_by_user(self, user: int) -> list:
        return UserGroup.objects.filter(user_id=user)

    @staticmethod
    def search_by_group(self, group: int) -> list:  # WARNING: Too many results
        return UserGroup.objects.filter(group_id=group)
