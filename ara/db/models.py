from django.db import models
from django.utils import timezone


class MetaDataQuerySet(models.QuerySet):
    def delete(self):
        return super().update(**{
            'deleted_at': timezone.now(),
        })

    def hard_delete(self):
        return super().delete()

    def bulk_create(self, objs, batch_size=None, ignore_conflicts=False):
        for obj in objs:
            if not hasattr(obj, 'created_at'):
                obj.created_at = timezone.now()

        return super().bulk_create(objs, batch_size)


class MetaDataManager(models.Manager):
    queryset_class = MetaDataQuerySet

    def get_queryset(self):
        return self.queryset_class(self.model).filter(deleted_at=timezone.datetime.min.replace(tzinfo=timezone.utc))


# TODO: add redis to metadatamodel
class MetaDataModel(models.Model):
    class Meta:
        abstract = True
        ordering = (
            '-created_at',
        )

    objects = MetaDataManager()

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='생성 시간',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        verbose_name='수정 시간',
    )
    deleted_at = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        db_index=True,
        verbose_name='삭제 시간',
    )

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

# Model for get_queryset all instance
class AllQueryMetaDataModel(models.Model):
    class Meta:
        abstract = True
        ordering = (
            '-created_at',
        )

    objects = MetaDataQuerySet.as_manager()

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        verbose_name='생성 시간',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_index=True,
        verbose_name='수정 시간',
    )
    deleted_at = models.DateTimeField(
        default=timezone.datetime.min.replace(tzinfo=timezone.utc),
        db_index=True,
        verbose_name='삭제 시간',
    )

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

class Search(models.Lookup):
   lookup_name = 'search'

   def as_mysql(self, compiler, connection):
       lhs, lhs_params = self.process_lhs(compiler, connection)
       rhs, rhs_params = self.process_rhs(compiler, connection)
       params = lhs_params + rhs_params
       return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params


models.CharField.register_lookup(Search)
models.TextField.register_lookup(Search)
