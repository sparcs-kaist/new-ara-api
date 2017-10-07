from django.db import models, IntegrityError

from ara.classes.model import MetaDataModel


class Article(MetaDataModel):
    class Meta:
        verbose_name = '문서'
        verbose_name_plural = '문서'

    title = models.CharField(
        max_length=256,
        verbose_name='제목',
    )
    content = models.TextField(
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

    hit_count = models.IntegerField(
        default=0,
        verbose_name='조회수',
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='좋아요 수',
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='싫어요 수',
    )

    created_by = models.ForeignKey(
        to='auth.User',
        db_index=True,
        related_name='article_set',
        verbose_name='작성자',
    )
    parent_topic = models.ForeignKey(
        to='core.Topic',
        null=True,
        blank=True,
        default=None,
        db_index=True,
        related_name='article_set',
        verbose_name='말머리',
    )
    parent_board = models.ForeignKey(
        to='core.Board',
        db_index=True,
        related_name='article_set',
        verbose_name='게시판',
    )

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            if self.parent_topic:
                assert self.parent_topic.parent_board == self.parent_board

        except AssertionError:
            raise IntegrityError('self.parent_board should be parent_board of self.parent_topic')

        super(Article, self).save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def update_vote_status(self):
        self.positive_vote_count = self.vote_set.filter(is_positive=True).count()
        self.negative_vote_count = self.vote_set.filter(is_positive=False).count()

        self.save()
