from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class vote(MetaDataModel):
    class Meta:
        verbose_name = '투표'
        verbose_name_plural = '투표'

    parent_article = models.ForeignKey(
        to='core.Article',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='vote',
        verbose_name='글',
    )
    parent_comment = models.ForeignKey(
        to='core.Comment',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='vote',
        verbose_name='댓글',
    )
    created_by = models.ForeignKey(
        to='auth.User',
        verbose_name='투표자',
    )
    is_up = models.BooleanField(
        verbose_name='찬반',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert self.parent_article==None != self.parent_comment==None

        except AssertionError:
            raise IntegrityError('self.parent_article and self.parent_comment should exist exclusively.')

        super(Article, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

