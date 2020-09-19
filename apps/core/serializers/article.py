from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext
from rest_framework import exceptions, serializers

from ara.classes.serializers import MetaDataModelSerializer

from apps.core.models import Article, Board, Scrap, ArticleReadLog
from apps.core.serializers.article_log import ArticleUpdateLogSerializer
from apps.core.serializers.board import BoardSerializer
from apps.core.serializers.topic import TopicSerializer


class BaseArticleSerializer(MetaDataModelSerializer):
    class Meta:
        model = Article
        exclude = ('content', 'content_text', 'migrated_hit_count', 'migrated_positive_vote_count', 'migrated_negative_vote_count',)

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

    @staticmethod
    def get_my_report(obj):
        from apps.core.serializers.report import BaseReportSerializer

        if not obj.report_set.exists():
            return None

        my_report = obj.report_set.all()[0]

        return BaseReportSerializer(my_report).data

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

    @staticmethod
    def get_created_by(obj):
        from apps.user.serializers.user import PublicUserSerializer

        if obj.is_anonymous:
            return '익명'

        data = PublicUserSerializer(obj.created_by).data
        data['is_blocked'] = obj.created_by.blocked_by_set.exists()

        return data

    @staticmethod
    def get_read_status(obj):
        if not obj.article_read_log_set.exists():
            return 'N'

        my_article_read_log = obj.article_read_log_set.all()[0]

        # compare with article's last commented datetime
        if obj.commented_at:
            if obj.commented_at > my_article_read_log.last_read_at:
                return 'U'

        # compare with article's last updated datetime
        if obj.article_update_log_set.exists():
            last_article_update_log = obj.article_update_log_set.all()[0]

            if last_article_update_log.created_at > my_article_read_log.last_read_at:
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

        if obj.created_by.blocked_by_set.exists():
            errors.append(exceptions.ValidationError('차단한 사용자의 게시물입니다.'))

        if obj.is_content_sexual and not self.context['request'].user.profile.see_sexual:
            errors.append(exceptions.ValidationError('성인/음란성 내용의 게시물입니다.'))

        if obj.is_content_social and not self.context['request'].user.profile.see_social:
            errors.append(exceptions.ValidationError('정치/사회성 내용의 게시물입니다.'))

        if not obj.parent_board.group_has_access(self.context['request'].user.profile.group):
            errors.append(exceptions.ValidationError('접근 권한이 없는 게시판입니다.'))

        return errors


class SideArticleSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        pass

    nested_comments_count = serializers.ReadOnlyField()
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
    def search(queryset, search):
        return queryset.prefetch_related('created_by__profile').filter(
            models.Q(title__search=search) |
            models.Q(content_text__search=search) |
            models.Q(created_by__profile__nickname__search=search)
        ).distinct()

    # TODO: refactoring
    def get_side_articles(self, obj):
        request = self.context['request']
        from_view = request.query_params.get('from_view')
        search_query = request.query_params.get('search_query')
        if from_view is None:
            return {
                'before': None,
                'after': None
            }

        if from_view in ['all', 'board', 'user', 'scrap', 'recent']:
            if from_view == 'all':
                articles = Article.objects.all()

            elif from_view == 'board':
                articles = obj.parent_board.article_set.all()

            elif from_view == 'user':
                created_by_id = request.query_params.get('created_by')
                if created_by_id is None:
                    created_by_id = request.user.id
                articles = Article.objects.filter(created_by_id=created_by_id)

            elif from_view == 'scrap':
                articles = Article.objects.filter(
                    scrap_set__scrapped_by=request.user
                ).order_by('-scrap_set__created_at')

                if not articles.filter(id=obj.id).exists():
                    raise serializers.ValidationError(gettext("This article is not in user's scrap list."))

            elif from_view == 'recent':
                articles = Article.objects.filter(
                    article_read_log_set__read_by=request.user
                ).order_by('-article_read_log_set__created_at')

                if not articles.filter(id=obj.id).exists():
                    raise serializers.ValidationError(gettext('This article is never read by user.'))

            if search_query:
                articles = self.search(articles, search_query)

            articles = articles.exclude(id=obj.id)
            before = articles.filter(created_at__lte=obj.created_at).first()
            after = articles.filter(created_at__gte=obj.created_at).last()

            return {
                'before': SideArticleSerializer(before, context=self.context).data if before else None,
                'after': SideArticleSerializer(after, context=self.context).data if after else None,
            }

        else:
            raise serializers.ValidationError(gettext("Wrong value for parameter 'from_view'."))

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

    comments_count = serializers.ReadOnlyField()
    nested_comments_count = serializers.ReadOnlyField()

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
    my_report = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    read_status = serializers.SerializerMethodField(
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
    nested_comments_count = serializers.ReadOnlyField(
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
            'positive_vote_count',
            'negative_vote_count',
            'created_by',
            'parent_topic',
            'parent_board',
            'commented_at',
        )
