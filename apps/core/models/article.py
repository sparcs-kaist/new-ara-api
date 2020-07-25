import bs4
import bleach

from django.db import models, IntegrityError
from django.conf import settings

from ara.db.models import MetaDataModel


class Article(MetaDataModel):
    class Meta(MetaDataModel.Meta):
        verbose_name = '문서'
        verbose_name_plural = '문서 목록'

    title = models.CharField(
        max_length=256,
        verbose_name='제목',
    )
    content = models.TextField(
        verbose_name='본문',
    )
    content_text = models.TextField(
        editable=False,
        verbose_name='text 형식 본문',
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
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        db_index=True,
        related_name='article_set',
        verbose_name='작성자',
    )
    parent_topic = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Topic',
        null=True,
        blank=True,
        default=None,
        db_index=True,
        related_name='article_set',
        verbose_name='말머리',
    )
    parent_board = models.ForeignKey(
        on_delete=models.CASCADE,
        to='core.Board',
        db_index=True,
        related_name='article_set',
        verbose_name='게시판',
    )

    attachments = models.ManyToManyField(
        to='core.Attachment',
        blank=True,
        db_index=True,
        verbose_name='첨부 파일(들)',
    )

    commented_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='마지막 댓글 시간',
    )

    url = models.TextField(
        null=True,
        default=None,
        verbose_name='링크',
    )

    def __str__(self):
        return self.title

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            if self.parent_topic:
                assert self.parent_topic.parent_board == self.parent_board

        except AssertionError:
            raise IntegrityError('self.parent_board should be parent_board of self.parent_topic')

        self.content = self.sanitize(self.content)

        self.content_text = ' '.join(bs4.BeautifulSoup(self.content, features='html5lib').find_all(text=True))

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    # TODO: hit_count property should be cached
    def update_hit_count(self):
        self.hit_count = self.article_read_log_set.count()

        self.save()

    # TODO: positive_vote_count, negative_vote_count properties should be cached
    def update_vote_status(self):
        self.positive_vote_count = self.vote_set.filter(is_positive=True).count()
        self.negative_vote_count = self.vote_set.filter(is_positive=False).count()

        self.save()

    @property
    def comments_count(self):
        from apps.core.models import Comment

        return Comment.objects.filter(parent_article=self).count()

    @property
    def nested_comments_count(self):
        from apps.core.models import Comment

        return Comment.objects.filter(
            models.Q(parent_article=self) |
            models.Q(parent_comment__parent_article=self)
        ).count()

    @staticmethod
    def sanitize(content):
        #allowed_tags = bleach.ALLOWED_TAGS + [u'p', u'pre', u'span', u'h1', u'h2', u'br']

        return content #bleach.linkify(bleach.clean(content, tags=allowed_tags))
