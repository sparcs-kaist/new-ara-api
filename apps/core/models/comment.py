import bleach

from django.db import models, IntegrityError
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from ara.db.models import MetaDataModel
from ara.sanitizer import sanitize


class Comment(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '댓글'
        verbose_name_plural = '댓글 목록'

    content = models.TextField(
        default=None,
        verbose_name='본문',
    )

    is_anonymous = models.BooleanField(
        default=False,
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
        db_index=True,
        verbose_name='임시 삭제 시간',
    )

    def __str__(self):
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
    
    @transaction.atomic
    def update_report_count(self):
        from apps.core.models import Report

        count = Report.objects.filter(parent_comment=self).count()

        self.report_count = count

        if int(count % settings.REPORT_THRESHOLD) == 0:
            self.hidden_at = timezone.now()

        self.save() 
