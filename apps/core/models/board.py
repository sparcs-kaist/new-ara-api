from enum import IntEnum, IntFlag, auto

from django.db import models
from django_extensions.db.fields import AutoSlugField

from ara.db.models import MetaDataModel


class NameType(IntFlag):
    REGULAR = auto()
    ANONYMOUS = auto()
    REALNAME = auto()


class BoardAccessPermissionType(IntEnum):
    READ = 0
    WRITE = 1
    COMMENT = 2


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
    # 사용자 그룹에 대해 접근 권한을 제어하는 bit mask 입니다.
    # access_mask & (1 << user.group) > 0 일 때 접근이 가능합니다.
    # 사용자 그룹의 값들은 `UserGroup`을 참고하세요.
    read_access_mask = models.SmallIntegerField(
        # UNAUTHORIZED, EXTERNAL_ORG 제외 모든 사용자 읽기 권한 부여
        verbose_name="읽기 권한",
        default=0b011011110,
    )
    write_access_mask = models.SmallIntegerField(
        # UNAUTHORIZED, STORE_EMPLOYEE, EXTERNAL_ORG 제외 모든 사용자 쓰기 권한 부여
        verbose_name="쓰기 권한",
        default=0b011011010,
    )
    comment_access_mask = models.SmallIntegerField(
        # UNAUTHORIZED 제외 모든 사용자 댓글 권한 부여
        verbose_name="댓글 권한",
        default=0b011111110,
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
    group_id = models.IntegerField(
        verbose_name="그룹 ID",
        default=1,
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
    top_threshold = models.SmallIntegerField(
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

    def group_has_access_permission(
        self, access_type: BoardAccessPermissionType, group: int
    ) -> bool:
        mask = None
        if access_type == BoardAccessPermissionType.READ:
            mask = self.read_access_mask
        elif access_type == BoardAccessPermissionType.WRITE:
            mask = self.write_access_mask
        elif access_type == BoardAccessPermissionType.COMMENT:
            mask = self.comment_access_mask
        else:
            # TODO: Handle error
            return False

        return (mask & (1 << group)) > 0
