from django.db import models

from ara.db.models import MetaDataModel


class GlobalNotice(MetaDataModel):
    title = models.CharField()
    content = models.TextField()
    expired_at = models.DateTimeField()
