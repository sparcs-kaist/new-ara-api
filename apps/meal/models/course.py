from django.db import models
from ara.db.models import MetaDataModel


class Course(MetaDataModel):
    restaurant_name = models.CharField(
        verbose_name="식당 이름",
        max_length=32,
    )
    price = models.PositiveIntegerField(
        verbose_name="가격",
        blank=True,
        null=True,
    )
    date = models.DateField(
        verbose_name="날짜",
    )
    day = models.CharField(
        verbose_name="요일",
        max_length=16,
    )
    time = models.CharField(
        verbose_name="시간대(조식/중식/석식)",
        max_length=16,
    )