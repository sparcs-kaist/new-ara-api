import bs4

from django.db import models, IntegrityError
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext

from apps.user.views.viewsets import make_random_profile_picture
from ara.db.models import MetaDataModel
from ara.sanitizer import sanitize
from ara.settings import HASH_SECRET_VALUE


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
    comment_count = models.IntegerField(
        default=0,
        verbose_name='댓글 수',
    )
    positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='좋아요 수',
    )
    negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='싫어요 수',
    )

    migrated_hit_count = models.IntegerField(
        default=0,
        verbose_name='이전된 조회수',
    )
    migrated_positive_vote_count = models.IntegerField(
        default=0,
        verbose_name='이전된 좋아요 수',
    )
    migrated_negative_vote_count = models.IntegerField(
        default=0,
        verbose_name='이전된 싫어요 수',
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
        blank=True,
        default=None,
        verbose_name='링크',
    )

    content_updated_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='제목/본문/첨부파일 수정 시간',
    )

    def __str__(self) -> str:
        return self.title

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        try:
            if self.parent_topic:
                assert self.parent_topic.parent_board == self.parent_board

        except AssertionError:
            raise IntegrityError('self.parent_board should be parent_board of self.parent_topic')

        if not self.parent_board.is_readonly:
            self.content = sanitize(self.content)

        self.content_text = ' '.join(bs4.BeautifulSoup(self.content, features='html5lib').find_all(text=True))

        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def update_hit_count(self):
        self.hit_count = self.article_read_log_set.values('read_by').annotate(models.Count('read_by')).order_by('read_by__count',).count() + self.migrated_hit_count

        self.save()

    def update_comment_count(self):
        from apps.core.models import Comment

        self.comment_count = Comment.objects.filter(
            models.Q(parent_article=self) |
            models.Q(parent_comment__parent_article=self)
        ).count()

        self.save()

    def update_vote_status(self):
        self.positive_vote_count = self.vote_set.filter(is_positive=True).count() + self.migrated_positive_vote_count
        self.negative_vote_count = self.vote_set.filter(is_positive=False).count() + self.migrated_negative_vote_count

        self.save()

    @property
    def created_by_nickname(self):
        return self.created_by.profile.nickname

    # API 상에서 보이는 사용자 (익명일 경우 익명화된 글쓴이, 그 외는 그냥 글쓴이)
    @cached_property
    def postprocessed_created_by(self):
        if not self.is_anonymous:
            return self.created_by
        else:
            user_unique_num = self.created_by.id + self.id + int(HASH_SECRET_VALUE)
            user_unique_encoding = str(hex(user_unique_num)).encode('utf-8')
            user_profile_picture = make_random_profile_picture(hash(user_unique_encoding))

            return {
                'id': 0,
                'username': gettext('anonymous'),
                'profile': {
                    'picture': user_profile_picture,
                    'nickname': gettext('anonymous'),
                    'user': gettext('anonymous')
                },
            }

