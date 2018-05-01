from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class Block(MetaDataModel):
    class Meta:
        verbose_name = '차단'
        verbose_name_plural = '차단'

    blocked_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='block_set',
        verbose_name='차단한 사람',
    )

    user = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='blocked_by_set',
        verbose_name='차단당한 사람',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            assert self.blocked_by != self.user

        except AssertionError:
            raise IntegrityError('self.user must not be self.blocked_by.')

        super(Block, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

