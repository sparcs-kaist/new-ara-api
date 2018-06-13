from django.db import models

from django_mysql.models import JSONField

from ara.classes.model import MetaDataModel, MetaDataManager, MetaDataQuerySet


class CommentUpdateLogQuerySet(MetaDataQuerySet):
    def create(self, comment, updated_by):
        from apps.core.serializers.comment import BaseCommentSerializer

        return super().create(**{
            'data': BaseCommentSerializer(comment).data,
            'comment': comment,
            'updated_by': updated_by,
        })


class CommentUpdateLogManager(MetaDataManager):
    pass


class CommentUpdateLog(MetaDataModel):
    class Meta:
        verbose_name = '댓글 변경 기록'
        verbose_name_plural = '댓글 변경 기록'

    objects = CommentUpdateLogManager.from_queryset(queryset_class=CommentUpdateLogQuerySet)()

    data = JSONField()

    updated_by = models.ForeignKey(
        to='auth.User',
        related_name='comment_update_log_set',
        verbose_name='변경자',
    )
    comment = models.ForeignKey(
        to='core.Comment',
        related_name='comment_update_log_set',
        verbose_name='변경된 댓글',
    )

    def __str__(self):
        return str(self.updated_by) + "/" + str(self.comment)

    @classmethod
    def prefetch_comment_update_log_set(cls):
        return models.Prefetch(
            'comment_update_log_set',
            queryset=CommentUpdateLog.objects.order_by('-created_at'),
        )


class CommentDeleteLog(MetaDataModel):
    class Meta:
        verbose_name = '댓글 삭제 기록'
        verbose_name_plural = '댓글 삭제 기록'

    deleted_by = models.ForeignKey(
        to='auth.User',
        related_name='comment_delete_log_set',
        verbose_name='삭제자',
    )
    comment = models.ForeignKey(
        to='core.Comment',
        related_name='comment_delete_log_set',
        verbose_name='삭제된 댓글',
    )

    def __str__(self):
        return str(self.deleted_by) + "/" + str(self.comment)
