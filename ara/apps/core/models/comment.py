from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class Comment(MetaDataModel):
    class Meta:
        verbose_name = '댓글'
        verbose_name_plural = '댓글'


    content = models.TextField(
        default=None,
        verbose_name='본문',
    )

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name='익명',
    )
    is_content_sexual = models.BooleanField(
        default=False,
        verbose_name='성인/음란성 내용',
    )
    is_content_social = models.BooleanField(
        default=False,
        verbose_name='정치/사회성 내용',
    )
    use_signature = models.BooleanField(
        default=True,
        verbose_name='서명 사용',
    )
    parent_article = models.ForeignKey(
        to='core.Article',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='글',
    )
    parent_comment = models.ForeignKey(
        to='core.Comment',
        default=None,
        null=True,
        blank=True,
        db_index=True,
        related_name='comment_set',
        verbose_name='댓글',
    )
    created_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='comment_set',
        verbose_name='작성자',
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='좋아요 수',
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='싫어요 수',
    )
    attachment = models.ImageField(
       default=None,
       verbose_name='첨부 그림',
    )


    def __str__(self):
        return self.content

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        #print(self.parent_article)
        #print(self.parent_comment)
        try:
            assert (self.parent_article==None) != (self.parent_comment==None)

        except AssertionError:
            raise IntegrityError('self.parent_article and self.parent_comment should exist exclusively.')

        try:
            assert self.content!=None or self.attachment!=None

        except AssertionError:
            raise IntegrityError('self.content and self.attachment should exist.')

        super(Comment, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

