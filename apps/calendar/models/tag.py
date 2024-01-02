from django.db import models

from ara.db.models import MetaDataModel


class Tag(MetaDataModel):
    name = models.CharField(max_length=255, unique=True)
    color = models.CharField(max_length=7, default="#000000")
    calendar = models.ForeignKey(
        "Calendar", on_delete=models.SET_NULL, null=True, blank=True
    )
