from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from django.db import models
from django.dispatch import receiver


@receiver(models.signals.pre_delete, sender=get_user_model())
def prevent_delete_user(instance, **kwargs):
    instance.is_active = False
    instance.save()

    raise SuspiciousOperation(
        "Deleting user is not allowed because it can cause unexpected server fatal error"
        "The user's is_active field has been updated to False instead of deleting the user instance."
    )
