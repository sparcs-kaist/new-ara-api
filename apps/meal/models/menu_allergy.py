from django.db import models
from ara.db.models import MetaDataModel


class MenuAllergy(MetaDataModel):
    allergen_code = models.PositiveIntegerField(
        verbose_name="알러지 번호",
        black=True,
        null=True,
    )
    menu_id = models.ForeignKey(
        verbose_name="일반 메뉴",
        to ="meal.Menu",
        on_delete=models.CASCADE,
        related_name="allergy_set",
        db_index=True,
    )
    cafeteria_menu_id = models.ForeignKey(
        verbose_name="카페테리아 메뉴",
        to ="meal.CafeteriaMenu",
        on_delete=models.CASCADE,
        related_name="allergy_set",
        db_index=True,
    ) 