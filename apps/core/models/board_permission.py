from enum import IntEnum
from typing import Any

from django.conf import settings
from django.db import models

from apps.user.models import Group, UserProfile

from .board import Board


class BoardAccessPermissionType(IntEnum):
    DENY = 0
    READ = 1
    WRITE = 2
    COMMENT = 3
    DELETE = 4


class BoardAccessPermission:
    def __init__(
        self, target: UserProfile | Group, board: Board
    ) -> None:  # permission: [BoardAccessPermissionType]
        self.target = target
        self.board = board
        self.READ = False
        self.WRITE = False
        self.COMMENT = False
        self.DELETE = False
        self.DENY = False

    def setPermission(self, permission: BoardAccessPermissionType) -> None:
        if self.DENY:
            return

        if permission == BoardAccessPermissionType.DENY:
            self.DENY = True
            self.READ = False
            self.WRITE = False
            self.COMMENT = False
            self.DELETE = False
        elif permission == BoardAccessPermissionType.READ:
            self.READ = True
        elif permission == BoardAccessPermissionType.WRITE:
            self.WRITE = True
        elif permission == BoardAccessPermissionType.COMMENT:
            self.COMMENT = True
        elif permission == BoardAccessPermissionType.DELETE:
            self.DELETE = True


class BoardPermission(models.Model):
    class Meta:
        verbose_name = "BoardPermission"
        verbose_name_plural = "BoardPermissions"
        unique_together = (("groupid", "boardid", "permission"),)

    group_id = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Groups",
        db_index=True,
        related_name="group_id",
        verbose_name="group",
    )
    board_slug = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Board",
        db_index=True,
        related_name="slug",
        verbose_name="board",
    )
    permission: int = models.SmallIntegerField(
        verbose_name="permission",
        null=False,
    )

    @staticmethod
    def permission_list_by_group(group: Group, board: Board) -> bool:
        permissions = BoardAccessPermission(group, board)
        groupPerms = BoardPermission.objects.filter(groupid=group, boardid=board)
        for perm in groupPerms:
            permissions.setPermission(perm.permission)

        return permissions

    @staticmethod
    def permission_list_by_user(
        user: UserProfile, board: Board
    ) -> BoardAccessPermission:
        groups = user.groups
        permissions = BoardAccessPermission(user, board)
        for group in groups:
            groupPerms = BoardPermission.objects.filter(groupid=group, boardid=board)
            for perm in groupPerms:
                permissions.setPermission(perm.permission)

        return permissions
