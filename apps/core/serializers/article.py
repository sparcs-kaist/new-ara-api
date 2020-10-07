from django.db import models
from django.utils.translation import gettext
from rest_framework import exceptions, serializers

from apps.core.documents import ArticleDocument
from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Article, ArticleReadLog, Board, Block
from apps.core.serializers.board import BoardSerializer
from apps.core.serializers.topic import TopicSerializer


class BaseArticleSerializer(MetaDataModelSerializer):
    class Meta:
        model = Article
        exclude = ('content', 'content_text', 'attachments',
                   'migrated_hit_count', 'migrated_positive_vote_count', 'migrated_negative_vote_count',)

    @staticmethod
    def get_my_vote(obj):
        if not obj.vote_set.exists():
            return None

        my_vote = obj.vote_set.all()[0]

        return my_vote.is_positive

    @staticmethod
    def get_my_scrap(obj):
        from apps.core.serializers.scrap import BaseScrapSerializer

        if not obj.scrap_set.exists():
            return None

        my_scrap = obj.scrap_set.all()[0]

        return BaseScrapSerializer(my_scrap).data

    def get_is_hidden(self, obj):
        if self.validate_hidden(obj):
            return True

        return False

    def get_why_hidden(self, obj):
        errors = self.validate_hidden(obj)

        return [
            {
                'detail': error.detail,
            } for error in errors
        ]

    def get_title(self, obj):
        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.title

    def get_hidden_title(self, obj):
        if self.validate_hidden(obj):
            return obj.title

        return ''

    def get_content(self, obj):
        errors = self.validate_hidden(obj)

        if errors:
            return [error.detail for error in errors]

        return obj.content

    def get_hidden_content(self, obj):
        if self.validate_hidden(obj):
            return obj.content

        return ''

    def get_created_by(self, obj):
        from apps.user.serializers.user import PublicUserSerializer

        if obj.is_anonymous:
            return '익명'

        data = PublicUserSerializer(obj.created_by).data
        data['is_blocked'] = Block.is_blocked(blocked_by=self.context['request'].user, user=obj.created_by)

        return data

    def get_read_status(self, obj):
        request = self.context['request']
        if not obj.article_read_log_set.exists():
            return 'N'

        my_article_read_log = obj.article_read_log_set.all()[0]

        # compare with article's last commented datetime
        if obj.commented_at:
            if obj.commented_at > my_article_read_log.created_at:
                return 'U'

        # compare with article's last updated datetime
        if obj.content_updated_at and obj.content_updated_at > my_article_read_log.created_at:
            return 'U'

        return '-'

    # TODO: article_current_page property must be cached
    def get_article_current_page(self, obj):
        view = self.context.get('view')

        if view:
            queryset = view.filter_queryset(view.get_queryset()).filter(
                created_at__gt=obj.created_at,
            )

            return queryset.count() // view.paginator.page_size + 1

        return None

    def validate_hidden(self, obj: Article):
        errors = []
        request = self.context['request']

        if Block.is_blocked(blocked_by=request.user, user=obj.created_by):
            errors.append(exceptions.ValidationError('차단한 사용자의 게시물입니다.'))

        if obj.is_content_sexual and not request.user.profile.see_sexual:
            errors.append(exceptions.ValidationError('성인/음란성 내용의 게시물입니다.'))

        if obj.is_content_social and not request.user.profile.see_social:
            errors.append(exceptions.ValidationError('정치/사회성 내용의 게시물입니다.'))

        if not obj.parent_board.group_has_access(request.user.profile.group):
            errors.append(exceptions.ValidationError('접근 권한이 없는 게시판입니다.'))

        return errors


class SideArticleSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        pass

    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    parent_topic = TopicSerializer(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_title = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = ('migrated_hit_count', 'migrated_positive_vote_count', 'migrated_negative_vote_count',)

    @staticmethod
    def search_articles(queryset, search):
        title_articles = queryset.filter(id__in=ArticleDocument.get_id_set('title', search))
        content_articles = queryset.filter(id__in=ArticleDocument.get_id_set('content_text', search))
        nickname_articles = queryset.filter(id__in=ArticleDocument.get_id_set('created_by_nickname', search))
        qs = title_articles | content_articles | nickname_articles

        return qs.distinct()

    @staticmethod
    def filter_articles(obj, request):
        from_view = request.query_params.get('from_view')

        if from_view == 'user':
            created_by_id = request.query_params.get('created_by', request.user.id)
            return Article.objects.filter(created_by_id=created_by_id)

        elif from_view == 'board':
            parent_board = obj.parent_board
            return Article.objects.filter(parent_board=parent_board)

        elif from_view == 'topic':
            parent_topic = obj.parent_topic
            return Article.objects.filter(parent_topic=parent_topic)

        elif from_view == 'scrap':
            articles = Article.objects.filter(
                scrap_set__scrapped_by=request.user
            ).order_by('-scrap_set__created_at')

            if not articles.filter(id=obj.id).exists():
                raise serializers.ValidationError(gettext("This article is not in user's scrap list."))

            return articles

        return Article.objects.all()

    def get_side_articles(self, obj):
        request = self.context['request']

        from_view = request.query_params.get('from_view')
        if from_view is None:
            return {
                'before': None,
                'after': None
            }

        if from_view not in ['all', 'board', 'topic', 'user', 'scrap', 'recent']:
            raise serializers.ValidationError(gettext("Wrong value for parameter 'from_view'."))

        if from_view == 'recent':
            after, before = self.get_side_articles_of_recent_article(obj, request)

        else:
            articles = self.filter_articles(obj, request)

            if request.query_params.get('search_query'):
                articles = self.search_articles(articles, request.query_params.get('search_query'))

            articles = articles.exclude(id=obj.id)
            before = articles.filter(created_at__lte=obj.created_at).first()
            after = articles.filter(created_at__gte=obj.created_at).last()

        return {
            'before': SideArticleSerializer(before, context=self.context).data if before else None,
            'after': SideArticleSerializer(after, context=self.context).data if after else None,
        }

    @staticmethod
    def get_side_articles_of_recent_article(obj, request):
        article_read_log_set = obj.article_read_log_set.all()

        # 현재 ArticleReadLog
        curr_read_log_of_obj = article_read_log_set.filter(
            read_by=request.user,
        ).order_by('-created_at')[0]

        # 직전 ArticleReadLog
        last_read_log_of_obj = article_read_log_set.filter(
            read_by=request.user,
        ).order_by('-created_at')[1]

        # 특정 글의 마지막 ArticleReadLog 를 찾기 위한 Subquery
        last_read_log_of_article = ArticleReadLog.objects.filter(
            article=models.OuterRef('pk')
        ).order_by('-created_at')

        # 특정 글의 마지막 Article created_at 을 last_read_at 으로 annotate 하고, last_read_at 기준으로 정렬
        recent_articles = Article.objects.filter(
            article_read_log_set__read_by=request.user,
        ).annotate(
            last_read_at=models.Subquery(
                queryset=last_read_log_of_article.exclude(
                    id=curr_read_log_of_obj.id,  # 무한루프 방지를 위해서 마지막(현재 request) 조회 기록은 제외한다.
                ).values('created_at')[:1],
            ),
        ).order_by(
            '-last_read_at'
        ).distinct()

        if not recent_articles.filter(id=obj.id).exists():
            raise serializers.ValidationError(gettext('This article is never read by user.'))

        recent_articles = recent_articles.exclude(
            id=obj.id,  # 자기 자신 제거
        )

        # 사용자가 현재 읽고 있는 글의 바로 직전 조회 기록보다 먼저 읽은 것 중 첫 번째
        before = recent_articles.filter(
            last_read_at__lte=last_read_log_of_obj.created_at,
        ).order_by('-last_read_at').first()

        # 사용자가 현재 읽고 있는 글의 바로 직전 조회 기록보다 늦게 읽은 것 중 첫 번째
        after = recent_articles.filter(
            last_read_at__gte=last_read_log_of_obj.created_at,
        ).order_by('last_read_at').first()

        return after, before

    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )

    from apps.core.serializers.comment import ArticleNestedCommentListActionSerializer
    comments = ArticleNestedCommentListActionSerializer(
        many=True,
        read_only=True,
        source='comment_set',
    )

    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_title = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_content = serializers.SerializerMethodField(
        read_only=True,
    )
    my_vote = serializers.SerializerMethodField(
        read_only=True,
    )
    my_scrap = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    article_current_page = serializers.SerializerMethodField(
        read_only=True,
    )
    side_articles = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleListActionSerializer(BaseArticleSerializer):
    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )
    is_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    why_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    hidden_title = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    read_status = serializers.SerializerMethodField(
        read_only=True,
    )


class BestArticleListActionSerializer(BaseArticleSerializer):
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleCreateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = ('migrated_hit_count', 'migrated_positive_vote_count', 'migrated_negative_vote_count',)
        read_only_fields = (
            'hit_count',
            'comment_count',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'commented_at',
        )

    def validate_parent_board(self, board: Board):
        user_is_superuser = self.context['request'].user.is_superuser
        user_has_perm = board.group_has_access(self.context['request'].user.profile.group)
        if not user_is_superuser and board.is_readonly:
            raise serializers.ValidationError(gettext('This board is read only.'))
        if not user_has_perm:
            raise serializers.ValidationError(gettext('This board is only for KAIST members.'))
        return board


class ArticleUpdateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = ('migrated_hit_count', 'migrated_positive_vote_count', 'migrated_negative_vote_count',)
        read_only_fields = (
            'is_anonymous',
            'hit_count',
            'comment_count',
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_topic',
            'parent_board',
            'commented_at',
        )
