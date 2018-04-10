from django.db import models

from ara.classes.model import MetaDataModel


class UserProfile(MetaDataModel):
    sid = models.CharField(max_length=30)

    picture = models.ImageField(
        blank=True,
        verbose_name='프로필',
    )
    nickname = models.CharField(
        blank=True,
        max_length=128,
        verbose_name='닉네임',
    )
    signature = models.TextField(
        blank=True,
        verbose_name='서명',
    )
    see_sexual = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='성인/음란성 보기',
    )
    see_social = models.BooleanField(
        blank=True,
        default=False,
        verbose_name='정치/사회성 보기',
    )

    user = models.OneToOneField(
        to='auth.User',
        related_name='profile',
        verbose_name='사용자',
    )

    def __str__(self):
        return self.user.username
