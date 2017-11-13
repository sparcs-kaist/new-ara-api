from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class BlackList(MetaDataModel):
    class Meta:
        verbose_name = '유저 간 차단'
        verbose_name_plural = '유저 간 차단'

    black_from = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='block_set',
        verbose_name='차단한 사람',
    )
    black_to = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='blocked_by_set',
        verbose_name='차단당한 사람',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert self.black_from != self.black_to

        except AssertionError:
            raise IntegrityError('self.black_from must not be self.black_to.')

        super(BlackList, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

