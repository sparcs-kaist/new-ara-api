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


class StoreEventKind(str, Enum):
    CLOSED = "CLOSED" # 임시 휴무
    OPEN = "OPEN" # 정기 휴무일의 임시 영업


WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


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
    # {"mon": [{"open": "11:00", "close": "20:00"}], ..., "sun": []}. 빈 배열은 정기 휴무, 여러 구간은 브레이크 타임
    hours = models.JSONField(
        verbose_name = "영업시간",
        default = dict,
        blank = True,
    )
    hours_note = models.CharField(
        verbose_name = "영업시간 메모",
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

    # 우선순위: 진행 중인 임시 휴무 > 진행 중인 임시 영업 > 정규 영업시간 (KST)
    def open_state(self, now=None) -> dict:
        now = now or timezone.now()
        local = timezone.localtime(now)
        events = getattr(self, "current_events", None)
        if events is None:
            events = list(self.events.filter(starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gte=now)))
        else:
            events = [e for e in events if e.starts_at <= now]

        intervals = [
            (block.get("open", ""), block.get("close", ""))
            for block in (self.hours or {}).get(WEEKDAYS[local.weekday()], [])
        ]
        opened = next((e for e in events if e.kind == StoreEventKind.OPEN.value), None)
        if opened and opened.open_time and opened.close_time:
            intervals = [(opened.open_time.strftime("%H:%M"), opened.close_time.strftime("%H:%M"))]
        today_hours = ", ".join(f"{o}–{c}" for o, c in intervals) or None

        closed = next((e for e in events if e.kind == StoreEventKind.CLOSED.value), None)
        if closed:
            note = "임시 휴무"
            if closed.reason:
                note += f" · {closed.reason}"
            if closed.ends_at:
                note += f" ({timezone.localtime(closed.ends_at):%m/%d}까지)"
            return {"is_open": False, "open_note": note, "today_hours": today_hours}

        if not intervals:
            return {"is_open": False, "open_note": "오늘 휴무", "today_hours": None}
        current = local.strftime("%H:%M")
        for open_at, close_at in intervals:
            if open_at <= current < close_at:
                return {"is_open": True, "open_note": f"{close_at}까지 영업", "today_hours": today_hours}
        upcoming = next((o for o, _ in intervals if current < o), None)
        note = f"{upcoming} 영업 시작" if upcoming else "영업 종료"
        return {"is_open": False, "open_note": note, "today_hours": today_hours}

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
    is_signature = models.BooleanField(
        verbose_name = "대표 메뉴",
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


# 앱의 "영업 종료" 토글은 ends_at 이 없는 CLOSED 이벤트를 만들고 지우는 것으로 처리한다
class StoreEvent(MetaDataModel):
    store = models.ForeignKey(
        verbose_name = "업체",
        to = Store,
        on_delete = models.CASCADE,
        related_name = "events",
    )
    kind = models.CharField(
        verbose_name = "종류",
        max_length = 10,
        choices = [(kind.value, kind.name) for kind in StoreEventKind],
    )
    starts_at = models.DateTimeField(
        verbose_name = "시작",
    )
    # null 이면 다시 열 때까지
    ends_at = models.DateTimeField(
        verbose_name = "끝",
        null = True,
        blank = True,
    )
    reason = models.CharField(
        verbose_name = "사유",
        max_length = 100,
        blank = True,
        default = "",
    )
    # OPEN 일 때만
    open_time = models.TimeField(
        verbose_name = "임시 영업 시작",
        null = True,
        blank = True,
    )
    close_time = models.TimeField(
        verbose_name = "임시 영업 끝",
        null = True,
        blank = True,
    )

    class Meta(MetaDataModel.Meta):
        ordering = ("starts_at",)
