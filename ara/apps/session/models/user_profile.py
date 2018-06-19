from django.db import models

from ara.db.models import MetaDataModel


class UserProfile(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '유저 프로필'
        verbose_name_plural = '유저 프로필 목록'

    sid = models.CharField(max_length=30)

    picture = models.ImageField(
        null=True,
        blank=True,
        default=None,
        upload_to='user_profiles/pictures',
        verbose_name='프로필',
    )
    nickname = models.CharField(
        blank=True,
        default='',
        max_length=128,
        verbose_name='닉네임',
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
