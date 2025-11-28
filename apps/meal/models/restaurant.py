from django.db import models
from ara.db.models import MetaDataModel

"""
식당 이름 (말머리 처럼 수동 추가)
(id, name)
(1, "카이마루")
(2, "서맛골")
(3, "동맛골 1층")
(4, "동맛골 2층")
(5, "교수회관")
"""

class Restaurant(MetaDataModel):
    restaurant_name = models.CharField(
        verbose_name="식당 이름",
        max_length=32,
        unique=True,
    )

    def __str__(self):
        return self.restaurant_name