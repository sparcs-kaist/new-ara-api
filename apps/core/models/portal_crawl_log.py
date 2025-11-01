from django.db import models

from ara.db.models import MetaDataModel


class PortalCrawlLog(MetaDataModel):

    portal_post_no = models.PositiveBigIntegerField(
        verbose_name = "포탈 공지 번호",
        null = False,
        unique = True,
    )

    title = models.CharField(
        verbose_name="제목",
        max_length = 255,
    ),

    content = models.TextField(
        verbose_name="본문",
    )

    view_count = models.PositiveIntegerField(
        verbose_name="조회수",
        default=0,
    )

    writer_name = models.CharField(
        verbose_name="작성자 이름",
        max_length=256,
    )

    writer_department = models.CharField(
        verbose_name="작성자 소속",
        max_length=256,
    )

    writer_email = models.CharField(
        verbose_name="작성자 이메일",
        max_length=256,
    )

    # portal 내 게시판 정보
    board_name = models.CharField(
        verbose_name="게시판 이름",
        max_length=256,
    )

    board_no = models.IntegerField(
        verbose_name="게시판 번호",
    )

    num_attachments = models.IntegerField(
        verbose_name="첨부파일 개수",
        default=0,
    )

    # 가져온 포탈 공지에 해당하는 게시글
    article = models.ForeignKey(
        to="core.Article",
        on_delete=models.CASCADE,
        related_name="게시물",
        null=False,
    )
