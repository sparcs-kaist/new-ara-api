from django.conf import settings
from django.db import models

from ara.db.models import MetaDataManager, MetaDataModel, MetaDataQuerySet


class CommentUpdateLogQuerySet(MetaDataQuerySet):
    def create(self, comment, updated_by):
        from apps.core.serializers.comment import BaseCommentSerializer

        return super().create(
            **{
                "data": BaseCommentSerializer(comment).data,
                "comment": comment,
                "updated_by": updated_by,
            }
        )


class CommentUpdateLogManager(MetaDataManager):
    pass


class CommentUpdateLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "댓글 변경 기록"
        verbose_name_plural = "댓글 변경 기록 목록"

    objects = CommentUpdateLogManager.from_queryset(
        queryset_class=CommentUpdateLogQuerySet
    )()

    data = models.JSONField(default=dict)

    updated_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="comment_update_log_set",
        verbose_name="변경자",
    )
    comment = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Comment",
        related_name="comment_update_log_set",
        verbose_name="변경된 댓글",
    )

    def __str__(self) -> str:
        return str(self.updated_by) + "/" + str(self.comment)


class CommentDeleteLog(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = "댓글 삭제 기록"
        verbose_name_plural = "댓글 삭제 기록 목록"

    deleted_by = models.ForeignKey(
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        related_name="comment_delete_log_set",
        verbose_name="삭제자",
    )
    comment = models.ForeignKey(
        on_delete=models.CASCADE,
        to="core.Comment",
        related_name="comment_delete_log_set",
        verbose_name="삭제된 댓글",
    )

    def __str__(self) -> str:
        return str(self.deleted_by) + "/" + str(self.comment)
