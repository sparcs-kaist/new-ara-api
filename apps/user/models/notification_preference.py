from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel

# 푸시 알림 주제. 필드 이름과 같다
PUSH_KINDS = ("article_commented", "comment_commented", "chat_message", "delivery")


# 주제별 푸시 알림 설정. 끄면 푸시만 안 가고 알림함에는 남는다
# 저장한 적 없는 유저는 모두 켜짐으로 본다
class UserNotificationPreference(MetaDataModel):
    user = models.OneToOneField(
        verbose_name = "유저",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "notification_preference",
    )
    article_commented = models.BooleanField(
        verbose_name = "내 글에 댓글",
        default = True,
    )
    comment_commented = models.BooleanField(
        verbose_name = "내 댓글에 답글",
        default = True,
    )
    chat_message = models.BooleanField(
        verbose_name = "채팅 메시지",
        default = True,
    )
    delivery = models.BooleanField(
        verbose_name = "함께 배달 소식",
        default = True,
    )

    @classmethod
    def get_for(cls, user):
        return cls.objects.filter(user=user).first() or cls(user=user)

    @classmethod
    def filter_push_targets(cls, user_ids, kind: str) -> list[int]:
        assert kind in PUSH_KINDS, kind
        user_ids = list(user_ids)
        muted = set(cls.objects.filter(
            user_id__in=user_ids, **{kind: False},
        ).values_list("user_id", flat=True))
        return [user_id for user_id in user_ids if user_id not in muted]
