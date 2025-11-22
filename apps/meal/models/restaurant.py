from django.db import models
from ara.db.models import MetaDataModel

class Restaurant(MetaDataModel):
    restaurant_name = models.CharField(
        verbose_name="식당 이름",
        max_length=32,
        unique=True,
    )

    def __str__(self):
        return self.restaurant_name