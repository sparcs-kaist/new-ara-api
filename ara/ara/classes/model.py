import datetime

from django.db import models


class MetaDataManager(models.Manager):
    def get_queryset(self):
        queryset = super(MetaDataManager, self).get_queryset()

        queryset = queryset.filter(deleted_at=None)

        return queryset


class MetaDataModel(models.Model):
    class Meta:
        abstract = True

    created_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='생성 시간',
    )
    updated_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='수정 시간',
    )
    deleted_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='삭제 시간',
    )

    objects = MetaDataManager()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.created_at:
            self.created_at = datetime.datetime.now()

        self.updated_at = datetime.datetime.now()

        super(MetaDataModel, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = datetime.datetime.now()

        self.save()

        return self
