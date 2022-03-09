from django.db import models

from django_extensions.db.fields import AutoSlugField

from ara.db.models import MetaDataModel


class Board(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '게시판'
        verbose_name_plural = '게시판 목록'
        unique_together = (
            ('ko_name', 'deleted_at'),
            ('en_name', 'deleted_at'),
        )

    slug = AutoSlugField(
        populate_from=[
            'en_name',
        ],
    )
    ko_name = models.CharField(
        max_length=32,
        verbose_name='게시판 국문 이름',
    )
    en_name = models.CharField(
        max_length=32,
        verbose_name='게시판 영문 이름',
    )
    ko_description = models.TextField(
        verbose_name='게시판 국문 소개',
    )
    en_description = models.TextField(
        verbose_name='게시판 영문 소개',
    )

    # 사용자 그룹에 대해 접근 권한을 제어하는 bit mask 입니다.
    # access_mask & (1<<user.group) > 0 일 때 접근이 가능합니다.
    # 사용자 그룹의 값들은 `UserGroup`을 참고하세요.
    access_mask = models.IntegerField(
        default=2,  # 카이스트 구성원만 사용 가능
        null=False,
        verbose_name='접근 권한 값'
    )
    is_readonly = models.BooleanField(
        verbose_name='읽기 전용 게시판',
        help_text='활성화했을 때 관리자만 글을 쓸 수 있습니다. (ex. 포탈공지)',
        default=False
    )
    is_hidden = models.BooleanField(
        verbose_name='리스트 숨김 게시판',
        help_text='활성화했을 때 메인페이지 상단바 리스트에 나타나지 않습니다. (ex. 뉴아라공지)',
        default=False,
        db_index=True,
    )

    is_anonymous = models.BooleanField(
        verbose_name='익명 게시판',
        help_text='게시판의 글과 댓글들이 익명이도록 합니다.',
        default=False,
        db_index=True
    )

    group_id = models.IntegerField(
        verbose_name='그룹 ID',
        default=1
    )

    banner_image = models.ImageField(
        null=True,
        blank=True,
        default=None,
        upload_to='board/banner_images',
        verbose_name='게시판 배너 이미지',
    )

    ko_banner_description = models.TextField(
        null=True,
        blank=True,
        default=None,
        verbose_name='게시판 배너에 삽입되는 국문 소개',
    )

    en_banner_description = models.TextField(
        null=True,
        blank=True,
        default=None,
        verbose_name='게시판 배너에 삽입되는 영문 소개',
    )

    def __str__(self) -> str:
        return self.ko_name

    def group_has_access(self, group: int) -> bool:
        return (self.access_mask & (1 << group)) > 0
