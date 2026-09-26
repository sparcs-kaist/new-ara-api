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
    # 채팅 신고면 chat_room 이 항상 있다
    chat_room = models.ForeignKey(
        on_delete=models.CASCADE,
        to="chatting.ChatRoom",
        default=None,
        null=True,
        blank=True,
        related_name="report_set",
        verbose_name="신고된 채팅방",
    )
    chat_message = models.ForeignKey(
        on_delete=models.SET_NULL,
        to="chatting.ChatMessage",
        default=None,
        null=True,
        blank=True,
        related_name="report_set",
        verbose_name="신고된 채팅 메시지",
    )
    reported_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="report_set",
        verbose_name="신고자",
    )
    # 익명 번호는 화면용이라 저장하지 않고 유저로 푼다
    reported_user = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        default=None,
        null=True,
        blank=True,
        related_name="received_report_set",
        verbose_name="피신고자",
    )
    # admin 용 신고 시점 이메일 (API 로는 내려주지 않는다)
    reporter_email = models.CharField(
        max_length=254,
        blank=True,
        default="",
        verbose_name="신고자 이메일",
    )
    reported_email = models.CharField(
        max_length=254,
        blank=True,
        default="",
        verbose_name="피신고자 이메일",
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

    STATUS_PENDING = "PENDING"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"

    STATUS_CHOICES = (
        (STATUS_PENDING, "접수"),
        (STATUS_IN_PROGRESS, "처리 중"),
        (STATUS_DONE, "처리 완료"),
    )

    status = models.CharField(
        choices=STATUS_CHOICES,
        max_length=20,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name="처리 상태",
    )
    status_changed_at = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        verbose_name="상태 변경 시각",
    )
    handled_by = models.ForeignKey(
        on_delete=models.SET_NULL,
        to=settings.AUTH_USER_MODEL,
        default=None,
        null=True,
        blank=True,
        related_name="handled_report_set",
        verbose_name="처리자",
    )

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if self.chat_room_id is not None:
            valid = self.parent_article is None and self.parent_comment is None
        else:
            valid = (self.parent_article is None) != (self.parent_comment is None)
        if not valid:
            raise IntegrityError(
                "a report needs exactly one target: parent_article, parent_comment, or chat_room."
            )
        if self.reported_user_id is None and self.chat_room_id is None:
            self.reported_user_id = self.parent.created_by_id

        super(Report, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

    @property
    def target_type(self) -> str:
        if self.parent_article_id:
            return "article"
        if self.parent_comment_id:
            return "comment"
        return "chat_message" if self.chat_message_id else "chat_member"

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
