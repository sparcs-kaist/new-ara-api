from django.db import models, IntegrityError

from ara.db.models import MetaDataModel


class Report(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '신고'
        verbose_name_plural = '신고 목록'
        unique_together = (
            ('parent_article', 'reported_by', 'deleted_at'),
            ('parent_comment', 'reported_by', 'deleted_at'),
        )

    parent_article = models.ForeignKey(
        to='core.Article',
        default=None,
        null=True,
        blank=True,
        related_name='report_set',
        verbose_name='신고된 문서',
    )
    parent_comment = models.ForeignKey(
        to='core.Comment',
        default=None,
        null=True,
        blank=True,
        related_name='report_set',
        verbose_name='신고된 댓글',
    )
    reported_by = models.ForeignKey(
        to='auth.User',
        verbose_name='신고자',
    )
    content = models.TextField(
        blank=True,
        verbose_name='내용',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert (self.parent_article is None) != (self.parent_comment is None)

        except AssertionError:
            raise IntegrityError('self.parent_article and self.parent_comment should exist exclusively.')

        super(Report, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    @property
    def parent(self):
        return self.parent_article if self.parent_article else self.parent_comment

    @classmethod
    def prefetch_my_report(cls, user):
        return models.Prefetch(
            'report_set',
            queryset=Report.objects.filter(
                reported_by=user,
            ),
        )
