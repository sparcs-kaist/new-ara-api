from django.db import models
from ara.db.models import MetaDataModel


class CafeteriaMenu(MetaDataModel):
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
    day = models.CharField(
        verbose_name="요일",
        max_length=10,
    )
    time = models.CharField(
        verbose_name="시간대(조식/중식/석식)",
        max_length=10,
    )