import datetime

from django.db import models


class MetaDataQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if 'updated_at' not in kwargs.keys():
            kwargs.update({
                'updated_at': datetime.datetime.now(),
            })

        return super().update(**kwargs)

    def delete(self):
        return super().update(**{
            'deleted_at': datetime.datetime.now(),
        })

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        for obj in objs:
            if not hasattr(obj, 'created_at'):
                obj.created_at = datetime.datetime.now()

        return super().bulk_create(objs, batch_size)


class MetaDataManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = queryset.filter(
            deleted_at=datetime.datetime.min,
        )

        return queryset


class MetaDataModel(models.Model):
    class Meta:
        abstract = True
        ordering = (
            '-created_at',
        )

    objects = MetaDataManager.from_queryset(queryset_class=MetaDataQuerySet)()

    created_at = models.DateTimeField(
        default=datetime.datetime.min,
        verbose_name='생성 시간',
    )
    updated_at = models.DateTimeField(
        default=datetime.datetime.min,
        verbose_name='수정 시간',
    )
    deleted_at = models.DateTimeField(
        default=datetime.datetime.min,
        verbose_name='삭제 시간',
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self._state.adding:
            self.created_at = datetime.datetime.now()

        else:
            self.updated_at = datetime.datetime.now()

        super().save(force_insert, force_update, using, update_fields)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = datetime.datetime.now()

        self.save()
