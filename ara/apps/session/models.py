from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from apps.session.sparcssso import Client


is_beta = [False, True][int(settings.SSO_IS_BETA)]
sso_client = Client(settings.SSO_CLIENT_ID, settings.SSO_SECRET_KEY, is_beta=is_beta)


class UserProfile(models.Model):
    user = models.ForeignKey(User)

    # SPARCS SSO spec
    sid = models.CharField(max_length=30)

    def __str__(self):
        return self.user.username
