from enum import Enum

from django.conf import settings
from django.db import models

from ara.db.models import MetaDataModel
from apps.meal.models.cafeteria_menu import MealType


class MenuPhotoSource(str, Enum):
    USER = "USER"
    INSTAGRAM = "INSTAGRAM"

MAX_PHOTOS_PER_MEAL = 3


# 입주업체 직원(STORE_EMPLOYEE)이 올린 사진은 공식 사진
class MenuPhoto(MetaDataModel):
    restaurant = models.ForeignKey(
        verbose_name = "식당",
        to = "meal.Restaurant",
        on_delete = models.CASCADE,
        related_name = "menu_photos",
    )
    date = models.DateField(
        verbose_name = "날짜",
    )
    meal_time = models.CharField(
        verbose_name = "식사 시간대",
        max_length = 10,
        choices = [(meal_type.value, meal_type.name) for meal_type in MealType],
    )
    image = models.ImageField(
        verbose_name = "사진",
        upload_to = "meal/menu_photos",
    )
    comment = models.CharField(
        verbose_name = "한 줄 후기",
        max_length = 200,
        blank = True,
        default = "",
    )
    source = models.CharField(
        verbose_name = "출처",
        max_length = 20,
        choices = [(source.value, source.name) for source in MenuPhotoSource],
        default = MenuPhotoSource.USER.value,
    )
    # 자동 수집 사진은 작성자가 없다
    created_by = models.ForeignKey(
        verbose_name = "올린 사람",
        to = settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "menu_photos",
        null = True,
        blank = True,
    )

    class Meta(MetaDataModel.Meta):
        indexes = [
            models.Index(fields=["restaurant", "date", "meal_time"], name="menu_photo_meal"),
        ]

    @property
    def is_official(self) -> bool:
        from apps.user.models import UserProfile

        profile = getattr(self.created_by, "profile", None) if self.created_by_id else None
        return bool(profile and profile.group == UserProfile.UserGroup.STORE_EMPLOYEE)
