from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from ara.db.models import MetaDataModel
from apps.chatting.models.message import ChatMessage, ChatMessageType

# 익명 투표 / 결과 숨기기 / 마감은 필드를 추가하고 can_see_* 만 고친다
class ChatVote(MetaDataModel):
    message = models.OneToOneField(
        verbose_name = "투표 메시지",
        to = "chatting.ChatMessage",
        on_delete = models.CASCADE,
        related_name = "vote",
    )
    title = models.CharField(
        verbose_name = "투표 제목",
        max_length = 100,
    )
    # 1 이면 단일 선택, null 이면 제한 없음
    max_choices = models.PositiveSmallIntegerField(
        verbose_name = "최대 선택 수",
        null = True,
        blank = True,
        default = 1,
    )

    def can_see_voters(self, user) -> bool:
        return True

    def can_see_counts(self, user) -> bool:
        return True

    @classmethod
    @transaction.atomic
    def create_with_message(cls, chat_room, created_by, title: str, options: list[str], max_choices):
        message = ChatMessage.create(
            chat_room=chat_room,
            created_by=created_by,
            message_type=ChatMessageType.VOTE.value,
            message_content=f"[투표] {title}",
        )
        vote = cls.objects.create(message=message, title=title, max_choices=max_choices)
        ChatVoteOption.objects.bulk_create([
            ChatVoteOption(vote=vote, text=text, order=order)
            for order, text in enumerate(options)
        ])
        return vote

    # 빈 리스트면 투표 취소
    @transaction.atomic
    def cast(self, user, option_ids: list[int]) -> None:
        list(ChatVote.objects.select_for_update().filter(pk=self.pk).values_list("pk", flat=True))
        option_ids = set(option_ids)

        if self.max_choices is not None and len(option_ids) > self.max_choices:
            raise ValidationError(f"최대 {self.max_choices}개까지 선택할 수 있습니다.")

        valid_ids = set(self.options.filter(id__in=option_ids).values_list("id", flat=True))
        if valid_ids != option_ids:
            raise ValidationError("이 투표에 없는 선택지입니다.")

        my_ballots = ChatVoteBallot.objects.filter(option__vote=self, user=user)
        my_ballots.exclude(option_id__in=option_ids).delete()
        for option_id in option_ids:
            ChatVoteBallot.objects.get_or_create(option_id=option_id, user=user)


class ChatVoteOption(MetaDataModel):
    vote = models.ForeignKey(
        verbose_name = "투표",
        to = ChatVote,
        on_delete = models.CASCADE,
        related_name = "options",
    )
    text = models.CharField(
        verbose_name = "선택지 내용",
        max_length = 100,
    )
    order = models.PositiveSmallIntegerField(
        verbose_name = "선택지 순서",
    )

    class Meta(MetaDataModel.Meta):
        ordering = ("order",)


class ChatVoteBallot(MetaDataModel):
    option = models.ForeignKey(
        verbose_name = "선택지",
        to = ChatVoteOption,
        on_delete = models.CASCADE,
        related_name = "ballots",
    )
    user = models.ForeignKey(
        verbose_name = "투표한 유저",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "chat_vote_ballots",
    )

    class Meta(MetaDataModel.Meta):
        unique_together = (("option", "user", "deleted_at"),)
