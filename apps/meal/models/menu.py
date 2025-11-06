from django.db import models
from ara.db.models import MetaDataModel


class Menu(MetaDataModel):
    menu_name = models.TextField(
        verbose_name="메뉴명",
        black=True,
        null=True,
    )
    course_id = models.ForeignKey(
        verbose_name="코스",
        to ="meal.Course",
        on_delete=models.CASCADE,
        related_name="menu_set",
        db_index=True,
    )