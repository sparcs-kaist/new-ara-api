from django.conf import settings
from django.db import models


class Group(models.Model):
    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"

    group_id = models.AutoField(
        verbose_name="Group ID",
        primary_key=True,
        db_index=True,
        null=False,
    )
    name = models.CharField(
        verbose_name="Group name",
        max_length=32,
        null=False,
    )
    description = models.CharField(
        verbose_name="Group description",
        max_length=128,
        null=True,
    )
    is_official = models.BooleanField(
        verbose_name="공식 단체 또는 학생단체",
        default=False,
    )

    def __str__(self) -> str:
        return self.name

    @staticmethod
    def search_by_name(name: str) -> list["Group"]:
        return Group.objects.filter(name=name)

    @staticmethod
    def search_by_id(group_id: int) -> "Group":
        return Group.objects.get(group_id=group_id)
