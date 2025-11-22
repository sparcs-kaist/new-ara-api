from django.db import models
from ara.db.models import MetaDataModel
from enum import Enum


class MealType(str, Enum):
    BREAKFAST = "BREAKFAST" # 조식
    LUNCH = "LUNCH" # 중식
    DINNER = "DINNER" # 석식

class CafeteriaMenu(MetaDataModel):
    restaurant_id = models.ForeignKey(
        to="meal.Restaurant",
        on_delete=models.CASCADE,
        related_name="cafeteria_menus",
        verbose_name="식당 이름",
        db_index=True,
    )
    menu_name = models.TextField(
        verbose_name="메뉴명",
    )
    price = models.IntegerField(
        verbose_name="가격",
        blank=True,
        null=True,
    )
    date = models.DateField(
        verbose_name="날짜",
    )
    meal_time = models.CharField(
        verbose_name="식사 시간대",
        max_length=10,
        choices=[(meal_type.value, meal_type.name) for meal_type in MealType],
        null = True,
    )