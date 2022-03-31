import typing
from enum import Enum
from typing import Dict, Union
import hashlib
import json

from django.core.files.storage import default_storage
from django.db import models, IntegrityError
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.utils.functional import cached_property
from django.utils.translation import gettext

from apps.user.views.viewsets import NOUNS, get_profile_picture
from ara.classes.decorator import cache_by_user
from ara.db.models import MetaDataModel, MetaDataQuerySet
from ara.sanitizer import sanitize
from ara.settings import HASH_SECRET_VALUE
from .block import Block
from .report import Report


class CommentHiddenReason(Enum):
    REPORTED_CONTENT = 'REPORTED_CONTENT'
    BLOCKED_USER_CONTENT = 'BLOCKED_USER_CONTENT'
    DELETED_CONTENT = 'DELETED_CONTENT'


class Comment(MetaDataModel):
    objects = MetaDataQuerySet.as_manager()

    class Meta(MetaDataModel.Meta):
        verbose_name = '댓글'
        verbose_name_plural = '댓글 목록'

    content = models.TextField(
        default=None,
        verbose_name='본문',
    )

    is_anonymous = models.SmallIntegerField(
        default=0,
        verbose_name='익명',
    )

    report_count = models.IntegerField(
        default=0,
        verbose_name ='신고 수',
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='좋아요 수',
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='싫어요 수',
    )

    created_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name='comment_set',
        verbose_name='작성자',
    )
    attachment = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Attachment',
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='첨부 파일',
    )
    parent_article = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Article',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='글',
    )
    parent_comment = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Comment',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='댓글',
    )
    hidden_at = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        verbose_name='숨김 시간',
    )

    def __str__(self) -> str:
        return self.content

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert (self.parent_article is None) != (self.parent_comment is None)

        except AssertionError:
            raise IntegrityError('self.parent_article and self.parent_comment should exist exclusively.')

        try:
            assert not self.parent_comment or not self.parent_comment.parent_comment

        except AssertionError:
            raise IntegrityError('comment of comment of comment is not allowed')

        try:
            assert self.content is not None or self.attachment is not None

        except AssertionError:
            raise IntegrityError('self.content and self.attachment should exist.')

        self.content = sanitize(self.content)

        super(Comment, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    # TODO: positive_vote_count, negative_vote_count properties should be cached
    def update_vote_status(self):
        self.positive_vote_count = self.vote_set.filter(is_positive=True).count()
        self.negative_vote_count = self.vote_set.filter(is_positive=False).count()

        self.save()

    def get_parent_article(self):
        if self.parent_article:
            return self.parent_article

        return self.parent_comment.parent_article

    def is_hidden_by_reported(self) -> bool:
        return self.hidden_at != timezone.datetime.min.replace(tzinfo=timezone.utc)

    def is_deleted(self) -> bool:
        return self.deleted_at != timezone.datetime.min.replace(tzinfo=timezone.utc)
    
    @transaction.atomic
    def update_report_count(self):
        count = Report.objects.filter(parent_comment=self).count()
        self.report_count = count

        if count >= int(settings.REPORT_THRESHOLD):
            self.hidden_at = timezone.now()

        self.save() 
    
    # API 상에서 보이는 사용자 (익명일 경우 익명화된 글쓴이, 그 외는 그냥 글쓴이)
    @cached_property
    def postprocessed_created_by(self) -> Union[settings.AUTH_USER_MODEL, Dict]:
        if self.is_anonymous == 0:
            return self.created_by
        
        parent_article = self.get_parent_article()
        parent_article_id = parent_article.id
        parent_article_created_by_id = parent_article.created_by.id
        comment_created_by_id = self.created_by.id
        
        # 댓글 작성자는 (작성자 id + parent article id + 시크릿)을 해시한 값으로 구별합니다.
        user_unique_num = comment_created_by_id + parent_article_id + HASH_SECRET_VALUE
        user_unique_encoding = str(hex(user_unique_num)).encode('utf-8')
        user_hash = hashlib.sha224(user_unique_encoding).hexdigest()
        user_hash_int = int(user_hash[-4:], 16)
        user_profile_picture = get_profile_picture(user_hash_int)

        if self.is_anonymous == 1:
            if parent_article_created_by_id == comment_created_by_id:
                user_name = gettext('author')
            else:
                user_name = make_anonymous_name(user_hash_int, user_hash[-3:])

            return {
                'id': user_hash,
                'username': user_name,
                'profile': {
                    'picture': default_storage.url(user_profile_picture),
                    'nickname': user_name,
                    'user': user_hash
                }
            }
        
        if self.is_anonymous == 2:
            sso_info = self.created_by.profile.sso_user_info
            user_realname = json.loads(sso_info["kaist_info"])["ku_kname"] if sso_info["kaist_info"] else sso_info["last_name"] + sso_info["first_name"]

            return {
                'id': user_unique_num,
                'username': user_realname,
                'profile': {
                    'picture': default_storage.url(user_profile_picture),
                    'nickname': user_realname,
                    'user': user_realname
                },
            }


    @cache_by_user
    def hidden_reasons(self, user: settings.AUTH_USER_MODEL) -> typing.List:
        reasons: typing.List[CommentHiddenReason] = []

        if self.is_deleted():
            reasons.append(CommentHiddenReason.DELETED_CONTENT)
        if self.is_hidden_by_reported():
            reasons.append(CommentHiddenReason.REPORTED_CONTENT)
        if Block.is_blocked(blocked_by=user, user=self.created_by):
            reasons.append(CommentHiddenReason.BLOCKED_USER_CONTENT)

        return reasons


def make_anonymous_name(hash_val, unique_tail) -> str:
    nickname = '익명의 ' + NOUNS[hash_val % len(NOUNS)] + ' ' + unique_tail
    return nickname
