from enum import IntFlag, auto

from django.db import models
from django_extensions.db.fields import AutoSlugField

from apps.user.models import Group
from ara.db.models import MetaDataModel

from .board_group import BoardGroup
from .board_permission import (
    DEFAULT_PERMISSIONS,
    BoardAccessPermission,
    BoardPermission,
)


class NameType(IntFlag):
    REGULAR = auto()
    ANONYMOUS = auto()
    REALNAME = auto()


class Board(MetaDataModel):
    slug = AutoSlugField(
        populate_from=["en_name"],
        unique=True,
    )
    ko_name = models.CharField(
        verbose_name="게시판 국문 이름",
        max_length=32,
    )
    en_name = models.CharField(
        verbose_name="게시판 영문 이름",
        max_length=32,
    )
    is_readonly = models.BooleanField(
        verbose_name="읽기 전용 게시판",
        default=False,
        help_text="활성화했을 때 관리자만 글을 쓸 수 있습니다. (ex. 포탈공지)",
    )
    is_hidden = models.BooleanField(
        verbose_name="리스트 숨김 게시판",
        db_index=True,
        default=False,
        help_text="활성화했을 때 메인페이지 상단바 리스트에 나타나지 않습니다. (ex. 뉴아라공지)",
    )

    name_type = models.SmallIntegerField(
        verbose_name="닉네임/익명/실명글 허용 여부 설정",
        db_index=True,
        default=NameType.REGULAR,
        help_text="글과 댓글을 어떤 이름 설정(닉네임/익명/실명)으로 작성할 수 있는지 정의합니다.",
    )
    is_school_communication = models.BooleanField(
        verbose_name="학교와의 소통 게시판",
        db_index=True,
        default=False,
        help_text="학교 소통 게시판 글임을 표시",
    )
    group: BoardGroup = models.ForeignKey(
        to="core.BoardGroup",
        on_delete=models.SET_NULL,
        related_name="boards",
        verbose_name="게시판 그룹",
        null=True,
        default=None,
    )
    banner_image = models.ImageField(
        verbose_name="게시판 배너 이미지",
        upload_to="board_banner_images",
        default="default_banner.png",
    )
    ko_banner_description = models.TextField(
        verbose_name="게시판 배너에 삽입되는 국문 소개",
        blank=True,
        default="",
    )
    en_banner_description = models.TextField(
        verbose_name="게시판 배너에 삽입되는 영문 소개",
        blank=True,
        default="",
    )
    top_threshold = models.PositiveSmallIntegerField(
        verbose_name="인기글 달성 기준 좋아요 개수",
        default=10,
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = "게시판"
        verbose_name_plural = "게시판 목록"
        unique_together = (
            ("ko_name", "deleted_at"),
            ("en_name", "deleted_at"),
        )

    def __str__(self) -> str:
        return self.ko_name

    def permission_list_by_group(self, group: Group) -> BoardAccessPermission:
        return BoardPermission.permission_list_by_group(group, self)

    def permission_list_by_user(self, user) -> BoardAccessPermission:
        return BoardPermission.permission_list_by_user(user, self)

    def set_default_permission(self):
        BoardPermission.add_permission_bulk_by_board(self, DEFAULT_PERMISSIONS)
