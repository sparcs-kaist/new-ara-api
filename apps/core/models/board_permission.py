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


DEFAULT_READ_PERMISSION: list[tuple[int, BoardAccessPermissionType]] = [
    (2, BoardAccessPermissionType.READ),
    (3, BoardAccessPermissionType.READ),
    (4, BoardAccessPermissionType.READ),
    (5, BoardAccessPermissionType.READ),
    (7, BoardAccessPermissionType.READ),
    (8, BoardAccessPermissionType.READ),
]
DEFAULT_WRITE_PERMISSION: list[tuple[int, BoardAccessPermissionType]] = [
    (2, BoardAccessPermissionType.WRITE),
    (4, BoardAccessPermissionType.WRITE),
    (5, BoardAccessPermissionType.WRITE),
    (7, BoardAccessPermissionType.WRITE),
    (8, BoardAccessPermissionType.WRITE),
]
DEFAULT_COMMENT_PERMISSION: list[tuple[int, BoardAccessPermissionType]] = [
    (2, BoardAccessPermissionType.COMMENT),
    (3, BoardAccessPermissionType.COMMENT),
    (4, BoardAccessPermissionType.COMMENT),
    (5, BoardAccessPermissionType.COMMENT),
    (6, BoardAccessPermissionType.COMMENT),
    (7, BoardAccessPermissionType.COMMENT),
    (8, BoardAccessPermissionType.COMMENT),
]


class BoardAccessPermission:
    def __init__(self, target: UserProfile | Group, board: Board) -> None:
        self.user = target if isinstance(target, UserProfile) else None
        self.group = target if isinstance(target, Group) else None
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

    @staticmethod
    def add_permission(
        group: Group,
        board: Board,
        permission: BoardAccessPermissionType,
    ):
        BoardPermission.objects.create(
            group=group,
            board=board,
            permission=permission,
        )

    @staticmethod
    def remove_permission(
        group: Group,
        board: Board,
        permission: BoardAccessPermissionType,
    ):
        BoardPermission.objects.filter(
            group=group,
            board=board,
            permission=permission,
        ).delete()

    @staticmethod
    def add_permission_bulk_by_board(
        board: Board,
        perms: list[tuple[int, BoardAccessPermissionType]],
    ):
        for group_id, perm in perms:
            BoardPermission.objects.create(
                group=Group.search_by_id(group_id),
                board=board,
                permission=perm,
            )

    @staticmethod
    def set_group_permission(permission: BoardAccessPermission):
        if permission.group is None:
            # raise ValueError("permission.group is None")
            return
        BoardPermission.objects.filter(
            group=permission.group, board=permission.board
        ).delete()
        if permission.DENY:
            BoardPermission.objects.create(
                group=permission.group,
                board=permission.board,
                permission=BoardAccessPermissionType.DENY,
            )
            return
        if permission.READ:
            BoardPermission.objects.create(
                group=permission.group,
                board=permission.board,
                permission=BoardAccessPermissionType.READ,
            )
        if permission.WRITE:
            BoardPermission.objects.create(
                group=permission.group,
                board=permission.board,
                permission=BoardAccessPermissionType.WRITE,
            )
        if permission.COMMENT:
            BoardPermission.objects.create(
                group=permission.group,
                board=permission.board,
                permission=BoardAccessPermissionType.COMMENT,
            )
        if permission.DELETE:
            BoardPermission.objects.create(
                group=permission.group,
                board=permission.board,
                permission=BoardAccessPermissionType.DELETE,
            )
