from django.db import models
from django.utils import timezone


class MetaDataQuerySet(models.QuerySet):
    def delete(self):
        """Delete the records in the current QuerySet."""
        self._not_support_combined_queries('delete')
        assert not self.query.is_sliced, \
            "Cannot use 'limit' or 'offset' with delete."

        if self._fields is not None:
            raise TypeError("Cannot call delete() after .values() or .values_list()")

        del_query = self._chain()

        # The delete is actually 2 queries - one to find related objects,
        # and one to delete. Make sure that the discovery of related
        # objects is performed on the same database as the deletion.
        del_query._for_write = True

        # Disable non-supported fields.
        del_query.query.select_for_update = False
        del_query.query.select_related = False
        del_query.query.clear_ordering(force_empty=True)

        # Changed in MetaDataQuerySet: collector = Collector(using=del_query.db)
        collector = MetaDataCollector(using=del_query.db)
        collector.collect(del_query)
        deleted, _rows_count = collector.delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return deleted, _rows_count

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


class MetaDataCollector(models.deletion.Collector):
    def hard_delete(self):
        return super().delete()


# TODO: add redis to metadatamodel
class MetaDataModel(models.Model):
    class Meta:
        abstract = True
        ordering = (
            '-created_at',
        )

    objects = MetaDataManager()

    created_at = models.DateTimeField(
        auto_now_add=True,
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
        using = using or router.db_for_write(self.__class__, instance=self)
        assert self.pk is not None, (
            "%s object can't be deleted because its %s attribute is set to None." %
            (self._meta.object_name, self._meta.pk.attname)
        )

        # Changed in MetaDataModel: collector = Collector(using=using)
        collector = MetaDataCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.delete()

    delete.alters_data = True

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    hard_delete.alters_data = True


class Search(models.Lookup):
   lookup_name = 'search'

   def as_mysql(self, compiler, connection):
       lhs, lhs_params = self.process_lhs(compiler, connection)
       rhs, rhs_params = self.process_rhs(compiler, connection)
       params = lhs_params + rhs_params
       return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params


models.CharField.register_lookup(Search)
models.TextField.register_lookup(Search)
