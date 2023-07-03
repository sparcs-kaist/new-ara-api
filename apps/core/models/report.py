from django.conf import settings
from django.db import IntegrityError, models
from django.utils.functional import cached_property

from ara.db.models import MetaDataModel


class Report(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "신고"
        verbose_name_plural = "신고 목록"
        unique_together = (
            ("parent_article", "reported_by", "deleted_at"),
            ("parent_comment", "reported_by", "deleted_at"),
        )

    TYPE_VIOLATION_OF_CODE = "violation_of_code"  # 커뮤니티 강령 위반 (욕설, 성적대상화 등)
    TYPE_IMPERSONATION = "impersonation"  # 사칭
    TYPE_INSULT = "insult"  # 명예훼손 및 모욕
    TYPE_SPAM = "spam"  # 스팸
    TYPE_OTHERS = "others"  # 기타
    TYPE_CHOICES = (
        (TYPE_VIOLATION_OF_CODE, "violation_of_code"),
        (TYPE_IMPERSONATION, "impersonation"),
        (TYPE_INSULT, "insult"),
        (TYPE_SPAM, "spam"),
        (TYPE_OTHERS, "others"),
    )

    parent_article = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Article",
        default=None,
        null=True,
        blank=True,
        related_name="report_set",
        verbose_name="신고된 게시물",
    )
    parent_comment = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Comment",
        default=None,
        null=True,
        blank=True,
        related_name="report_set",
        verbose_name="신고된 댓글",
    )
    reported_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="report_set",
        verbose_name="신고자",
    )
    type = models.CharField(
        choices=TYPE_CHOICES,
        max_length=128,
        blank=True,
        default="",
    )
    content = models.TextField(
        blank=True,
        verbose_name="내용",
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

        super(Report, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @cached_property
    def parent(self):
        return self.parent_article if self.parent_article else self.parent_comment

    @classmethod
    def prefetch_my_report(cls, user, prefix="") -> models.Prefetch:
        return models.Prefetch(
            "{}report_set".format(prefix),
            queryset=Report.objects.filter(
                reported_by=user,
            ),
        )
