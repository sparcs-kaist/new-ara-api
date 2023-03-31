import typing
from enum import Enum
from typing import Dict, Union

import bs4
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext

from apps.user.views.viewsets import get_profile_picture, hashlib
from ara.classes.decorator import cache_by_user
from ara.db.models import MetaDataModel
from ara.sanitizer import sanitize
from ara.settings import (
    ANSWER_PERIOD,
    HASH_SECRET_VALUE,
    MIN_TIME,
    SCHOOL_RESPONSE_VOTE_THRESHOLD,
)

from .block import Block
from .board import BoardAccessPermissionType, BoardNameType
from .comment import Comment
from .communication_article import SchoolResponseStatus
from .report import Report


class ArticleHiddenReason(str, Enum):
    ADULT_CONTENT = "ADULT_CONTENT"
    SOCIAL_CONTENT = "SOCIAL_CONTENT"
    REPORTED_CONTENT = "REPORTED_CONTENT"
    BLOCKED_USER_CONTENT = "BLOCKED_USER_CONTENT"
    ACCESS_DENIED_CONTENT = "ACCESS_DENIED_CONTENT"


class Article(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "게시물"
        verbose_name_plural = "게시물 목록"

    title = models.CharField(
        max_length=256,
        verbose_name="제목",
    )
    content = models.TextField(
        verbose_name="본문",
    )
    content_text = models.TextField(
        editable=False,
        verbose_name="text 형식 본문",
    )

    name_type = models.SmallIntegerField(
        default=BoardNameType.REGULAR,
        verbose_name="익명 혹은 실명 여부",
    )
    is_content_sexual = models.BooleanField(
        default=False,
        verbose_name="성인/음란성 내용",
    )
    is_content_social = models.BooleanField(
        default=False,
        verbose_name="정치/사회성 내용",
    )

    hit_count = models.IntegerField(
        default=0,
        verbose_name="조회수",
    )
    comment_count = models.IntegerField(
        default=0,
        verbose_name="댓글 수",
    )
    report_count = models.IntegerField(
        default=0,
        verbose_name="신고 수",
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name="좋아요 수",
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name="싫어요 수",
    )

    migrated_hit_count = models.IntegerField(
        default=0,
        verbose_name="이전된 조회수",
    )
    migrated_positive_vote_count = models.IntegerField(
        default=0,
        verbose_name="이전된 좋아요 수",
    )
    migrated_negative_vote_count = models.IntegerField(
        default=0,
        verbose_name="이전된 싫어요 수",
    )

    created_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name="article_set",
        verbose_name="작성자",
    )
    parent_topic = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Topic",
        null=True,
        blank=True,
        default=None,
        db_index=True,
        related_name="article_set",
        verbose_name="말머리",
    )
    parent_board = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Board",
        db_index=True,
        related_name="article_set",
        verbose_name="게시판",
    )

    attachments = models.ManyToManyField(
        to="core.Attachment",
        blank=True,
        db_index=True,
        verbose_name="첨부 파일(들)",
    )

    commented_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="마지막 댓글 시간",
    )

    url = models.URLField(
        null=True,
        max_length=200,
        blank=True,
        default=None,
        verbose_name="포탈 링크",
    )

    content_updated_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name="제목/본문/첨부파일 수정 시간",
    )

    hidden_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        verbose_name="숨김 시간",
    )

    def __str__(self):
        return self.title

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        try:
            if self.parent_topic:
                assert self.parent_topic.parent_board == self.parent_board

        except AssertionError:
            raise IntegrityError(
                "self.parent_board should be parent_board of self.parent_topic"
            )

        if not self.parent_board.is_readonly:
            self.content = sanitize(self.content)

        self.content_text = " ".join(
            bs4.BeautifulSoup(self.content, features="html5lib").find_all(text=True)
        )

        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    def update_hit_count(self):
        self.hit_count = (
            self.article_read_log_set.values("read_by")
            .annotate(models.Count("read_by"))
            .order_by(
                "read_by__count",
            )
            .count()
            + self.migrated_hit_count
        )

        self.save()

    def update_comment_count(self):
        self.comment_count = (
            Comment.objects.filter(deleted_at=MIN_TIME)
            .filter(
                models.Q(parent_article=self)
                | models.Q(parent_comment__parent_article=self)
            )
            .count()
        )

        self.save()

    @transaction.atomic
    def update_report_count(self):
        count = Report.objects.filter(parent_article=self).count()
        self.report_count = count

        if count >= int(settings.REPORT_THRESHOLD):
            self.hidden_at = timezone.now()

        self.save()

    def update_vote_status(self):
        self.positive_vote_count = (
            self.vote_set.filter(is_positive=True).count()
            + self.migrated_positive_vote_count
        )
        self.negative_vote_count = (
            self.vote_set.filter(is_positive=False).count()
            + self.migrated_negative_vote_count
        )

        if (
            self.parent_board.is_school_communication
            and self.positive_vote_count >= SCHOOL_RESPONSE_VOTE_THRESHOLD
            and self.communication_article.school_response_status
            == SchoolResponseStatus.BEFORE_UPVOTE_THRESHOLD
        ):
            self.communication_article.school_response_status = (
                SchoolResponseStatus.BEFORE_SCHOOL_CONFIRM
            )
            self.communication_article.response_deadline = (
                timezone.localtime() + timezone.timedelta(days=ANSWER_PERIOD + 1)
            ).date()
            self.communication_article.save()

        self.save()

    def is_hidden_by_reported(self) -> bool:
        return self.hidden_at is not None

    @property
    def created_by_nickname(self):
        return self.created_by.profile.nickname

    # API 상에서 보이는 사용자 (익명일 경우 익명화된 글쓴이, 그 외는 그냥 글쓴이)
    @cached_property
    def postprocessed_created_by(self) -> Union[settings.AUTH_USER_MODEL, Dict]:
        if self.name_type == BoardNameType.REGULAR:
            return self.created_by

        user_unique_num = self.created_by.id + self.id + HASH_SECRET_VALUE
        user_unique_encoding = str(hex(user_unique_num)).encode("utf-8")
        user_hash = hashlib.sha224(user_unique_encoding).hexdigest()
        user_hash_int = int(user_hash[-4:], 16)
        user_profile_picture = get_profile_picture(user_hash_int)

        if self.name_type == BoardNameType.ANONYMOUS:
            return {
                "id": user_hash,
                "username": gettext("anonymous"),
                "profile": {
                    "picture": default_storage.url(user_profile_picture),
                    "nickname": gettext("anonymous"),
                    "user": gettext("anonymous"),
                },
            }

        if self.name_type == BoardNameType.REALNAME:
            user_realname = self.created_by.profile.realname
            return {
                "id": user_unique_num,
                "username": user_realname,
                "profile": {
                    "picture": default_storage.url(user_profile_picture),
                    "nickname": user_realname,
                    "user": user_realname,
                },
            }

    @cache_by_user
    def hidden_reasons(self, user: settings.AUTH_USER_MODEL) -> typing.List:
        reasons = []
        if self.is_hidden_by_reported():
            reasons.append(ArticleHiddenReason.REPORTED_CONTENT)
        if Block.is_blocked(blocked_by=user, user=self.created_by):
            reasons.append(ArticleHiddenReason.BLOCKED_USER_CONTENT)
        if self.is_content_sexual and not user.profile.see_sexual:
            reasons.append(ArticleHiddenReason.ADULT_CONTENT)
        if self.is_content_social and not user.profile.see_social:
            reasons.append(ArticleHiddenReason.SOCIAL_CONTENT)
        # 혹시 몰라 여기 두기는 하는데 여기 오기전에 Permission에서 막혀야 함
        if not self.parent_board.group_has_access_permission(
            BoardAccessPermissionType.READ, user.profile.group
        ):
            reasons.append(ArticleHiddenReason.ACCESS_DENIED_CONTENT)

        return reasons
