from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel

class CommentUpdateLog(MetaDataModel):
    class Meta:
        verbose_name = '댓글 변경 기록'
        verbose_name_plural = '댓글 변경 기록'

    updated_by = models.ForeignKey(
        to='auth.User',
        related_name='comment_update_log_set',
        verbose_name='변경자',
    )

    content = models.TextField(
        default=None,
        verbose_name='본문',
    )
    attachment = models.ImageField(
        default=None,
        verbose_name='첨부 그림',
    )
    parent_comment = models.ForeignKey(
        to='core.Comment',
        related_name='comment_update_log_set',
        verbose_name='변경된 댓글',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert self.content!=None or self.attachment!=None

        except AssertionError:
            raise IntegrityError('self.content and self.attachment should exist.')

        super(CommentUpdateLog, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)




