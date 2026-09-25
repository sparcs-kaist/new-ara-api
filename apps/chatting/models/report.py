from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from ara.db.models import MetaDataModel
from apps.core.models.report import Report

# 같은 사람을 같은 방에서 다시 신고할 수 있기까지
REPORT_COOLDOWN = timedelta(hours=24)


# 채팅 신고. 게시글 / 댓글 신고(core.Report)와 규칙이 달라 따로 둔다
# 신고자는 피신고자에게 절대 노출되지 않는다. 이메일은 관리자가 admin 에서 바로 보도록 신고 시점 값을 남긴다
class ChatReport(MetaDataModel):
    reported_by = models.ForeignKey(
        verbose_name = "신고자",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "chat_reports_sent",
    )
    reported_user = models.ForeignKey(
        verbose_name = "피신고자",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "chat_reports_received",
    )
    chat_room = models.ForeignKey(
        verbose_name = "채팅방",
        to = "chatting.ChatRoom",
        on_delete = models.CASCADE,
        related_name = "report_set",
    )
    message = models.ForeignKey(
        verbose_name = "신고된 메시지",
        to = "chatting.ChatMessage",
        on_delete = models.SET_NULL,
        related_name = "report_set",
        null = True,
        blank = True,
    )
    reported_anon_number = models.PositiveIntegerField(
        verbose_name = "피신고자 익명 번호",
        null = True,
        blank = True,
    )
    type = models.CharField(
        verbose_name = "신고 사유",
        max_length = 128,
        choices = Report.TYPE_CHOICES,
    )
    content = models.TextField(
        verbose_name = "내용",
        blank = True,
        default = "",
    )
    reporter_email = models.CharField(
        verbose_name = "신고자 이메일 (신고 시점)",
        max_length = 254,
        blank = True,
        default = "",
    )
    reported_email = models.CharField(
        verbose_name = "피신고자 이메일 (신고 시점)",
        max_length = 254,
        blank = True,
        default = "",
    )

    class Meta(MetaDataModel.Meta):
        verbose_name = "채팅 신고"
        verbose_name_plural = "채팅 신고 목록"

    @classmethod
    def reported_recently(cls, reporter, reported_user, chat_room) -> bool:
        return cls.objects.filter(
            reported_by=reporter,
            reported_user=reported_user,
            chat_room=chat_room,
            created_at__gte=timezone.now() - REPORT_COOLDOWN,
        ).exists()
