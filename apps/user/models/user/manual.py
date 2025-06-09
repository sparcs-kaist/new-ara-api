from django.conf import settings
from django.db import models

from apps.user.models import Group
from ara.db.models import MetaDataModel


class ManualUser(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "수동 등록된 사용자"  # 단체 및 업체
        verbose_name_plural = "수동 등록된 사용자 목록"

    user = models.OneToOneField(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="manual",
        verbose_name="사용자",
        null=True,
        blank=True,
        default=None,
    )

    org_name = models.CharField(
        max_length=160,
        verbose_name="업체/단체 이름",
    )

    org_type: Group = models.ForeignKey(
        on_delete=models.CASCADE,
        to="user.Group",
        verbose_name="업체/단체 그룹",
    )

    applicant_name = models.CharField(
        max_length=160,
        verbose_name="신청자 이름",
    )

    sso_email = models.EmailField(
        max_length=160,
        unique=True,
        verbose_name="sso 이메일",
    )
