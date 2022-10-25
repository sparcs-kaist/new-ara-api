from cached_property import cached_property
from django.conf import settings
from django.db import IntegrityError, models

from ara.db.models import MetaDataModel


class Vote(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "투표"
        verbose_name_plural = "투표 목록"
        unique_together = (
            ("parent_article", "voted_by", "deleted_at"),
            ("parent_comment", "voted_by", "deleted_at"),
        )

    is_positive = models.BooleanField(
        verbose_name="찬반",
    )

    voted_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="vote_set",
        verbose_name="투표자",
    )
    parent_article = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Article",
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name="vote_set",
        verbose_name="상위 게시물",
    )
    parent_comment = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Comment",
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name="vote_set",
        verbose_name="상위 댓글",
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        try:
            assert (self.parent_article is None) != (self.parent_comment is None)

        except AssertionError:
            raise IntegrityError(
                "self.parent_article and self.parent_comment should exist exclusively."
            )

        super(Vote, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @cached_property
    def parent(self):
        return self.parent_article if self.parent_article else self.parent_comment

    @classmethod
    def prefetch_my_vote(cls, user, prefix="") -> models.Prefetch:
        return models.Prefetch(
            "{}vote_set".format(prefix),
            queryset=Vote.objects.filter(
                voted_by=user,
            ),
        )
