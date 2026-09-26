from enum import Enum

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from ara.db.models import MetaDataModel


class StoreZone(str, Enum):
    EAST = "EAST"
    WEST = "WEST"
    NORTH = "NORTH"


# 교내 입주 업체. 운영진이 admin 에서 만들고 StoreStaff 로 지정된 계정만 고친다
class Store(MetaDataModel):
    name = models.CharField(
        verbose_name = "업체 이름",
        max_length = 50,
    )
    intro = models.TextField(
        verbose_name = "소개",
        blank = True,
        default = "",
    )
    zone = models.CharField(
        verbose_name = "구역",
        max_length = 10,
        choices = [(zone.value, zone.name) for zone in StoreZone],
    )
    location = models.CharField(
        verbose_name = "위치 (건물 / 상세)",
        max_length = 100,
        blank = True,
        default = "",
    )
    hours = models.CharField(
        verbose_name = "운영 시간",
        max_length = 200,
        blank = True,
        default = "",
    )
    cover = models.ImageField(
        verbose_name = "대표 이미지",
        upload_to = "meal/stores",
        null = True,
        blank = True,
    )
    phone = models.CharField(
        verbose_name = "전화번호",
        max_length = 30,
        blank = True,
        default = "",
    )
    link = models.URLField(
        verbose_name = "링크",
        max_length = 500,
        blank = True,
        default = "",
    )
    # 카이마루 푸드코트처럼 학식 식당 안에 있는 업체
    restaurant = models.ForeignKey(
        verbose_name = "속한 식당",
        to = "meal.Restaurant",
        on_delete = models.SET_NULL,
        related_name = "stores",
        null = True,
        blank = True,
    )
    is_active = models.BooleanField(
        verbose_name = "운영 중",
        default = True,
    )
    order = models.PositiveIntegerField(
        verbose_name = "정렬 순서",
        default = 0,
    )

    class Meta(MetaDataModel.Meta):
        ordering = ("order", "id")

    def is_staff(self, user) -> bool:
        if not (user and user.is_authenticated):
            return False
        return user.is_staff or self.staff.filter(user=user).exists()

    def active_notices(self):
        now = timezone.now()
        return self.notices.filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        )


class StoreMenu(MetaDataModel):
    store = models.ForeignKey(
        verbose_name = "업체",
        to = Store,
        on_delete = models.CASCADE,
        related_name = "menus",
    )
    section = models.CharField(
        verbose_name = "분류",
        max_length = 30,
        blank = True,
        default = "",
    )
    name = models.CharField(
        verbose_name = "메뉴 이름",
        max_length = 50,
    )
    price = models.PositiveIntegerField(
        verbose_name = "가격",
        null = True,
        blank = True,
    )
    description = models.CharField(
        verbose_name = "설명",
        max_length = 200,
        blank = True,
        default = "",
    )
    photo = models.ImageField(
        verbose_name = "사진",
        upload_to = "meal/store_menus",
        null = True,
        blank = True,
    )
    is_sold_out = models.BooleanField(
        verbose_name = "품절",
        default = False,
    )
    order = models.PositiveIntegerField(
        verbose_name = "정렬 순서",
        default = 0,
    )

    class Meta(MetaDataModel.Meta):
        ordering = ("order", "id")


class StoreStaff(MetaDataModel):
    store = models.ForeignKey(
        verbose_name = "업체",
        to = Store,
        on_delete = models.CASCADE,
        related_name = "staff",
    )
    user = models.ForeignKey(
        verbose_name = "직원 계정",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "managed_stores",
    )

    class Meta(MetaDataModel.Meta):
        unique_together = (("store", "user", "deleted_at"),)


class StoreNotice(MetaDataModel):
    store = models.ForeignKey(
        verbose_name = "업체",
        to = Store,
        on_delete = models.CASCADE,
        related_name = "notices",
    )
    title = models.CharField(
        verbose_name = "제목",
        max_length = 100,
    )
    body = models.TextField(
        verbose_name = "내용",
        blank = True,
        default = "",
    )
    # 비어 있으면 기간 제한 없음
    starts_at = models.DateTimeField(
        verbose_name = "시작",
        null = True,
        blank = True,
    )
    ends_at = models.DateTimeField(
        verbose_name = "끝",
        null = True,
        blank = True,
    )
