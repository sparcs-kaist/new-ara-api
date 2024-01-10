from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models

import apps.core.models.board as board
from apps.user.models import Group, UserProfile

if TYPE_CHECKING:
    from .board import Board


class BoardAccessPermissionType(IntEnum):
    DENY = 0
    READ = 1
    WRITE = 2
    COMMENT = 3
    DELETE = 4


class BoardAccessPermission:
    def __init__(self, target: UserProfile | Group, board: Board) -> None:
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
        unique_together = (("group", "board", "permission"),)

    group = models.ForeignKey(
        on_delete=models.CASCADE,
        to="user.Group",
        db_index=True,
        verbose_name="group",
    )
    board = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Board",
        db_index=True,
        verbose_name="board slug",
    )
    permission: int = models.SmallIntegerField(
        verbose_name="permission",
        null=False,
    )

    @staticmethod
    def permission_list_by_group(group: Group, board: Board) -> BoardAccessPermission:
        permissions = BoardAccessPermission(group, board)
        groupPerms = BoardPermission.objects.filter(group=group, board=board)
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
            groupPerms = BoardPermission.objects.filter(group=group, board=board)
            for perm in groupPerms:
                permissions.setPermission(perm.permission)

        return permissions
