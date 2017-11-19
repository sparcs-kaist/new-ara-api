from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class Comment(MetaDataModel):
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글'

    content = models.TextField(
        default=None,
        verbose_name='본문',
    )

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='익명',
    )
    use_signature = models.BooleanField(
        default=True,
        verbose_name='서명 사용',
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='좋아요 수',
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='싫어요 수',
    )

    attachment = models.ForeignKey(
        to='core.Attachment',
        null=True,
        blank=True,
        db_index=True,
        verbose_name='첨부 파일',
    )
    created_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='comment_set',
        verbose_name='작성자',
    )
    parent_article = models.ForeignKey(
        to='core.Article',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='글',
    )
    parent_comment = models.ForeignKey(
        to='core.Comment',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='댓글',
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

        super(Comment, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def update_vote_status(self):
        self.positive_vote_count = self.vote_set.filter(is_positive=True).count()
        self.negative_vote_count = self.vote_set.filter(is_positive=False).count()

        self.save()
