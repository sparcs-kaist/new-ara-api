from rest_framework import serializers, exceptions
import typing
import hashlib

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Article, Comment, Block
from django.utils import timezone
from django.utils.translation import gettext
from ara.settings import HASH_SECRET_VALUE


class BaseCommentSerializer(MetaDataModelSerializer):
    class Meta:
        model = Comment
        exclude = ('attachment', )

    @staticmethod
    def get_my_vote(obj) -> typing.Optional[bool]:
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    def get_is_hidden(self, obj) -> bool:
        if self.validate_hidden(obj):
            return True

        return False

    def get_why_hidden(self, obj) -> typing.List[dict]:
        errors = self.validate_hidden(obj)

        return [
            {
                'detail': error.detail,
            } for error in errors
        ]

    def get_content(self, obj) -> typing.Union[str, list]:
        if self.get_is_hidden_by_reported(obj):
            return gettext('This comment is hidden because it received multiple reports')

        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.content

    def get_hidden_content(self, obj) -> str:
        if self.get_is_hidden_by_reported(obj):
            return gettext('This comment is hidden because it received multiple reports')
            
        if self.validate_hidden(obj):
            return obj.content

        return ''

    @staticmethod
    def get_created_by(obj) -> typing.Union[str, dict]:
        from apps.user.serializers.user import PublicUserSerializer

        if obj.is_anonymous:
            return get_anonymous_user(obj) # 게시글 작성자의 댓글은 '글쓴이'로 표시

        # <class 'rest_framework.utils.serializer_helpers.ReturnDict'> (is an OrderedDict)
        return PublicUserSerializer(obj.created_by).data

    def validate_hidden(self, obj) -> typing.List[exceptions.ValidationError]:
        errors = []

        if Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by):
            errors.append(exceptions.ValidationError(gettext('This article is written by a시 user you blocked.')))

        return errors

    def get_is_hidden_by_reported(self, obj:Comment) -> bool:
        return obj.hidden_at != timezone.datetime.min.replace(tzinfo=timezone.utc)


def get_parent_article(obj) -> Article:
    if obj.parent_article:
        print('parent article writer', obj.parent_article.created_by.id)
        return obj.parent_article
    else:
        parent_comment_id = obj.parent_comment.id
        parent_article = Comment.objects.get(id=parent_comment_id).parent_article
        return parent_article


def get_anonymous_user(obj) -> dict:

    parent_article = get_parent_article(obj)
    parent_article_id = parent_article.id
    parent_article_created_by_id = parent_article.created_by.id
    comment_created_by_id = obj.created_by.id

    # 댓글 작성자는 (작성자 id + parent article id + 시크릿)을 해시한 값으로 구별합니다.
    user_unique_num = comment_created_by_id + parent_article_id + int(HASH_SECRET_VALUE)
    user_unique_encoding = str(hex(user_unique_num)).encode('utf-8')
    user_hash = hashlib.sha224(user_unique_encoding).hexdigest()
    user_profile_picture = make_random_profile_picture(hash(user_unique_encoding))

    if parent_article_created_by_id == comment_created_by_id:
        user_name = gettext('글쓴이') # TODO: 번역
    else:
        user_name = make_anonymous_name(hash(user_unique_encoding), user_hash[-3:])

    return {
        'id': user_hash,
        'username': user_name,
        'profile': {
            'picture': user_profile_picture,
            'nickname': user_name,
            'user': user_hash
        }
    }


def make_anonymous_name(hash_val, unique_tail) -> str:
    nouns = ['외계인', '펭귄', '코뿔소', '여우', '염소', '타조', '사과', '포도', '다람쥐', '도토리', '해바라기', '코끼리', '돌고래', '거북이', '나비',
             '앵무새', '알파카', '강아지', '고양이', '원숭이', '두더지', '낙타', '망아지', '시조새', '힙스터', '로봇', '감자', '고구마', '가마우지', '직박구리',
             '오리너구리', '보노보노', '개미핥기', '치타', '사자', '구렁이', '도마뱀', '개구리', '올빼미', '부엉이']

    nickname = '익명의 ' + nouns[hash_val % len(nouns)] + ' ' + unique_tail
    return nickname


def make_random_profile_picture(hash_val) -> str:
    colors = ['blue', 'red', 'gray']
    numbers = ['1', '2', '3']

    temp_color = colors[hash_val % len(colors)]
    temp_num = numbers[hash_val % len(numbers)]
    default_picture = f'user_profiles/default_pictures/{temp_color}-default{temp_num}.png'

    return default_picture


class CommentSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentListActionSerializer(BaseCommentSerializer):
    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class CommentNestedCommentListActionSerializer(CommentListActionSerializer):
    pass


class ArticleNestedCommentListActionSerializer(CommentListActionSerializer):
    comments = CommentNestedCommentListActionSerializer(
        many=True,
        read_only=True,
        source='comment_set',
    )


class CommentCreateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )


class CommentUpdateActionSerializer(BaseCommentSerializer):
    class Meta(BaseCommentSerializer.Meta):
        read_only_fields = (
            'is_anonymous',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_article',
            'parent_comment',
        )

    from apps.user.serializers.user import PublicUserSerializer
    created_by = PublicUserSerializer(
        read_only=True,
    )
