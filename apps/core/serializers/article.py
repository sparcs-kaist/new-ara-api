import datetime
from enum import Enum

from django.utils import timezone
from django.utils.translation import gettext
from rest_framework import exceptions, serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from apps.core.documents import ArticleDocument
from apps.core.models import Article, ArticleHiddenReason, Block, Board, Comment, Scrap
from apps.core.models.board import BoardAccessPermissionType, NameType
from apps.core.models.article_metadata import ArticleMetadata
from apps.core.serializers.attachment import AttachmentSerializer
from apps.core.serializers.board import BoardSerializer
from apps.core.serializers.article_metadata import (
    BaseArticleMetadataSerializer,
    ArticleMetadataSerializer,
)
from apps.core.serializers.mixins.hidden import (
    HiddenSerializerFieldMixin,
    HiddenSerializerMixin,
)
from apps.core.serializers.topic import TopicSerializer
from apps.user.serializers.user import PublicUserSerializer
from ara.classes.serializers import MetaDataModelSerializer


class BaseArticleSerializer(HiddenSerializerMixin, MetaDataModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.CAN_OVERRIDE_REASONS = [
            ArticleHiddenReason.SOCIAL_CONTENT,
            ArticleHiddenReason.ADULT_CONTENT,
            ArticleHiddenReason.BLOCKED_USER_CONTENT,
        ]

    class Meta:
        model = Article
        exclude = (
            "content",
            "content_text",
            "attachments",
            "migrated_hit_count",
            "migrated_positive_vote_count",
            "migrated_negative_vote_count",
        )

    def get_my_vote(self, obj) -> bool | None:
        request = self.context["request"]
        if not obj.vote_set.filter(voted_by=request.user).exists():
            return None

        my_vote = obj.vote_set.filter(voted_by=request.user)[0]

        return my_vote.is_positive

    @staticmethod
    def get_my_scrap(obj) -> dict | None:
        from apps.core.serializers.scrap import BaseScrapSerializer

        if not obj.scrap_set.exists():
            return None

        my_scrap = obj.scrap_set.all()[0]

        return BaseScrapSerializer(my_scrap).data

    def get_title(self, obj) -> str | None:
        if self.visible_verdict(obj):
            return obj.title
        return None

    def get_content(self, obj) -> str | None:
        if self.visible_verdict(obj):
            return obj.content
        return None

    def get_created_by(self, obj) -> dict:
        if obj.name_type in (NameType.ANONYMOUS, NameType.REALNAME):
            return obj.postprocessed_created_by
        else:
            data = PublicUserSerializer(obj.postprocessed_created_by).data
            data["is_blocked"] = Block.is_blocked(
                blocked_by=self.context["request"].user, user=obj.created_by
            )
            return data

    @staticmethod
    def get_read_status(obj) -> str:
        if not obj.article_read_log_set.exists():
            return "N"

        my_article_read_log = obj.article_read_log_set.all()[0]

        # compare with article's last commented datetime
        if obj.commented_at:
            if obj.commented_at > my_article_read_log.created_at:
                return "U"

        # compare with article's last updated datetime
        if (
            obj.content_updated_at
            and obj.content_updated_at > my_article_read_log.created_at
        ):
            return "U"

        return "-"

    # TODO: article_current_page property must be cached
    def get_article_current_page(self, obj) -> int | None:
        view = self.context.get("view")

        if view:
            queryset = view.filter_queryset(view.get_queryset()).filter(
                created_at__gt=obj.created_at,
            )

            return queryset.count() // view.paginator.page_size + 1
        return None

    metadata = serializers.SerializerMethodField(read_only=True)

    def get_metadata(self, obj):
        # article_metadata_set으로 접근 (related_name)
        metadata = obj.article_metadata_set.first()
        if metadata:
            return ArticleMetadataSerializer(metadata).data
        return None


class SideArticleSerializer(HiddenSerializerFieldMixin, BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        pass

    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    can_override_hidden = serializers.SerializerMethodField(
        read_only=True,
    )
    parent_topic = TopicSerializer(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleSerializer(HiddenSerializerFieldMixin, BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = (
            "migrated_hit_count",
            "migrated_positive_vote_count",
            "migrated_negative_vote_count",
            "content_text",
        )

    @staticmethod
    def search_articles(queryset, search):
        return queryset.filter(id__in=ArticleSerializer.search_article_id_set(search))

    @staticmethod
    def search_article_id_set(search):
        return ArticleDocument.get_main_search_id_set(search)

    @staticmethod
    def filter_articles(obj, request):
        from_view = request.query_params.get("from_view")

        if from_view == "-portal":
            return Article.objects.exclude(parent_board__slug="portal-notice")

        elif from_view == "user":
            created_by_id = request.query_params.get("created_by", request.user.id)
            return Article.objects.filter(created_by_id=created_by_id)

        elif from_view == "board":
            parent_board = obj.parent_board
            return Article.objects.filter(parent_board=parent_board)

        elif from_view == "topic":
            parent_topic = obj.parent_topic
            return Article.objects.filter(parent_topic=parent_topic)

        elif from_view == "scrap":
            articles = Article.objects.filter(
                scrap_set__scrapped_by=request.user
            ).order_by("-scrap_set__created_at")
            if not articles.filter(id=obj.id).exists():
                raise serializers.ValidationError(
                    gettext("This article is not in user's scrap list.")
                )
            return articles

        elif from_view == "top":
            current_date = datetime.datetime.combine(
                timezone.now().date(), datetime.time.min, datetime.timezone.utc
            )
            # get the articles that are created_at within a week and order by hit_count
            top_articles = Article.objects.filter(
                created_at__gte=current_date - datetime.timedelta(days=7)
            ).order_by("-hit_count", "-pk")

            if not top_articles.filter(id=obj.id).exists():
                raise serializers.ValidationError(
                    gettext("This article is not in top articles.")
                )
            return top_articles

        return Article.objects.all()

    def get_side_articles(self, obj) -> dict:
        request = self.context["request"]

        from_view = request.query_params.get("from_view")
        if from_view is None:
            return {"before": None, "after": None}

        if from_view not in [
            "all",
            "-portal",
            "board",
            "topic",
            "user",
            "scrap",
            "recent",
            "top",
        ]:
            raise serializers.ValidationError(
                gettext("Wrong value for parameter 'from_view'.")
            )

        if from_view == "recent":
            after, before = self.get_side_articles_of_recent_article(obj, request)

        else:
            articles = self.filter_articles(obj, request)
            if request.query_params.get("search_query"):
                articles = self.search_articles(
                    articles, request.query_params.get("search_query")
                )
            articles = articles.exclude(id=obj.id)

            if from_view == "scrap":
                scrap_obj_created_at = obj.scrap_set.get(
                    scrapped_by=request.user
                ).created_at

                scrap_list = Scrap.objects.filter(scrapped_by=request.user).exclude(
                    parent_article_id=obj.id
                )
                before_scrap = scrap_list.filter(
                    created_at__lte=scrap_obj_created_at
                ).first()
                after_scrap = scrap_list.filter(
                    created_at__gte=scrap_obj_created_at
                ).last()

                if before_scrap:
                    before = before_scrap.parent_article
                else:
                    before = None

                if after_scrap:
                    after = after_scrap.parent_article
                else:
                    after = None
            elif from_view == "top":
                before = articles.filter(created_at__lte=obj.created_at).first()
                after = articles.filter(created_at__gte=obj.created_at).last()
            else:
                before = articles.filter(created_at__lte=obj.created_at).first()
                after = articles.filter(created_at__gte=obj.created_at).last()

        return {
            "before": (
                SideArticleSerializer(before, context=self.context).data
                if before
                else None
            ),
            "after": (
                SideArticleSerializer(after, context=self.context).data
                if after
                else None
            ),
        }

    def get_side_articles_of_recent_article(self, obj, request):
        article_user_read_log_set = obj.article_read_log_set.filter(
            read_by=request.user,
        ).order_by("-created_at")[:2]

        if len(article_user_read_log_set) < 2:
            return None, None
        curr_read_log_of_obj, last_read_log_of_obj = article_user_read_log_set

        search_restriction_sql = ""
        if request.query_params.get("search_query"):
            recent_articles = self.search_article_id_set(
                request.query_params.get("search_query")
            )
            search_restriction_sql = "AND `core_articlereadlog`.`article_id` IN %s"
            query_params = [
                request.user.id,
                obj.id,
                recent_articles,
                last_read_log_of_obj.created_at,
            ]
        else:
            query_params = [request.user.id, obj.id, last_read_log_of_obj.created_at]

        before_query = f"""
        SELECT * FROM `core_article`
        JOIN (
            SELECT `core_articlereadlog`.`article_id`, MAX(`core_articlereadlog`.`created_at`) AS my_last_read_at
            FROM `core_articlereadlog`
            WHERE (
                `core_articlereadlog`.`deleted_at` = '0001-01-01 00:00:00' AND
                `core_articlereadlog`.`read_by_id` = %s AND
                `core_articlereadlog`.`article_id` <> %s
                {search_restriction_sql}
            )
            GROUP BY `core_articlereadlog`.`article_id`
            ORDER BY my_last_read_at desc
        ) recents ON recents.article_id = `core_article`.id
        WHERE recents.my_last_read_at <= %s
        ORDER BY recents.my_last_read_at desc LIMIT 1
        """

        after_query = f"""
        SELECT * FROM `core_article`
        JOIN (
            SELECT `core_articlereadlog`.`article_id`, MAX(`core_articlereadlog`.`created_at`) AS my_last_read_at
            FROM `core_articlereadlog`
            WHERE (
                `core_articlereadlog`.`deleted_at` = '0001-01-01 00:00:00' AND
                `core_articlereadlog`.`read_by_id` = %s AND
                `core_articlereadlog`.`article_id` <> %s
                {search_restriction_sql}
            )
            GROUP BY `core_articlereadlog`.`article_id`
            ORDER BY my_last_read_at desc
        ) recents ON recents.article_id = `core_article`.id
        WHERE recents.my_last_read_at >= %s
        ORDER BY recents.my_last_read_at asc LIMIT 1
        """

        before = [v for v in Article.objects.raw(before_query, query_params)]
        before = None if len(before) == 0 else before[0]
        after = [v for v in Article.objects.raw(after_query, query_params)]
        after = None if len(after) == 0 else after[0]
        return after, before

    def get_attachments(self, obj: Article) -> ReturnDict | None:
        if self.visible_verdict(obj):
            attachments = obj.attachments.all()
            serializer = AttachmentSerializer(attachments, many=True)
            return serializer.data
        return None

    def get_my_comment_profile(self, obj):
        created_by = self.context["request"].user
        name_type = obj.name_type

        if (
            obj.parent_board.is_school_communication
            and created_by.profile.is_school_admin
        ):
            name_type = NameType.REGULAR

        fake_comment = Comment(
            created_by=created_by,
            name_type=name_type,
            parent_article=obj,
        )
        if fake_comment.name_type in (
            NameType.ANONYMOUS,
            NameType.REALNAME,
        ):
            return fake_comment.postprocessed_created_by
        else:
            data = PublicUserSerializer(fake_comment.postprocessed_created_by).data
            return data

    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )

    attachments = serializers.SerializerMethodField(
        read_only=True,
    )

    my_comment_profile = serializers.SerializerMethodField(read_only=True)

    from apps.core.serializers.comment import ArticleNestedCommentListActionSerializer

    comments = ArticleNestedCommentListActionSerializer(
        many=True,
        read_only=True,
        source="comment_set",
    )

    is_mine = serializers.SerializerMethodField(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    content = serializers.SerializerMethodField(
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
    communication_article_status = serializers.SerializerMethodField(
        read_only=True,
    )

    days_left = serializers.SerializerMethodField(
        read_only=True,
    )

    @staticmethod
    def get_days_left(obj):
        if hasattr(obj, "communication_article"):
            return obj.communication_article.days_left
        return None

    @staticmethod
    def get_communication_article_status(obj):
        if hasattr(obj, "communication_article"):
            return obj.communication_article.school_response_status
        return None


class ArticleAttachmentType(Enum):
    NONE = "NONE"
    IMAGE = "IMAGE"
    NON_IMAGE = "NON_IMAGE"
    BOTH = "BOTH"


class ArticleListActionSerializer(HiddenSerializerFieldMixin, BaseArticleSerializer):
    parent_topic = TopicSerializer(
        read_only=True,
    )
    parent_board = BoardSerializer(
        read_only=True,
    )
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )
    read_status = serializers.SerializerMethodField(
        read_only=True,
    )

    attachment_type = serializers.SerializerMethodField(
        read_only=True,
    )

    communication_article_status = serializers.SerializerMethodField(
        read_only=True,
    )

    days_left = serializers.SerializerMethodField(
        read_only=True,
    )

    def get_attachment_type(self, obj) -> str:
        if not self.visible_verdict(obj):
            return ArticleAttachmentType.NONE.value

        has_image = False
        has_non_image = False
        for att in obj.attachments.all():
            if att.mimetype[:5] == "image":
                has_image = True
            else:
                has_non_image = True
        if has_image and has_non_image:
            return ArticleAttachmentType.BOTH.value
        if has_image:
            return ArticleAttachmentType.IMAGE.value
        if has_non_image:
            return ArticleAttachmentType.NON_IMAGE.value
        return ArticleAttachmentType.NONE.value

    @staticmethod
    def get_communication_article_status(obj):
        if hasattr(obj, "communication_article"):
            return obj.communication_article.school_response_status
        return None

    @staticmethod
    def get_days_left(obj):
        if hasattr(obj, "communication_article"):
            return obj.communication_article.days_left
        return None


class BestArticleListActionSerializer(
    HiddenSerializerFieldMixin, BaseArticleSerializer
):
    title = serializers.SerializerMethodField(
        read_only=True,
    )
    created_by = serializers.SerializerMethodField(
        read_only=True,
    )


class ArticleCreateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = (
            "migrated_hit_count",
            "migrated_positive_vote_count",
            "migrated_negative_vote_count",
            "content_text",
        )
        read_only_fields = (
            "hit_count",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "created_by",
            "commented_at",
        )

    def validate_parent_board(self, board: Board):
        user_is_superuser = self.context["request"].user.is_superuser
        if not user_is_superuser and board.is_readonly:
            raise serializers.ValidationError(gettext("This board is read only."))
        user_has_write_permission = board.group_has_access_permission(
            BoardAccessPermissionType.WRITE, self.context["request"].user.profile.group
        )
        if not user_has_write_permission:
            raise exceptions.PermissionDenied()
        return board

    def create(self, validated_data):
        article = super().create(validated_data)

        # 요청에 metadata가 포함된 경우에만 생성
        metadata = self.initial_data.get('metadata')
        if metadata:
            if not isinstance(metadata, dict):
                raise serializers.ValidationError({"metadata": "메타데이터는 유효한 JSON 형식이어야 합니다."})
            ArticleMetadata.objects.create(
                article=article,
                metadata=metadata
            )

        return article


class ArticleUpdateActionSerializer(BaseArticleSerializer):
    class Meta(BaseArticleSerializer.Meta):
        exclude = (
            "migrated_hit_count",
            "migrated_positive_vote_count",
            "migrated_negative_vote_count",
            "content_text",
        )
        read_only_fields = (
            "name_type",
            "hit_count",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "created_by",
            "parent_topic",
            "parent_board",
            "commented_at",
        )

    def update(self, instance, validated_data):
        article = super().update(instance, validated_data)
        
        # metadata 필드가 요청에 포함된 경우에만 처리
        if 'metadata' in self.initial_data:
            metadata = self.initial_data.get('metadata')
            if not isinstance(metadata, dict):
                raise serializers.ValidationError({"metadata": "메타데이터는 유효한 JSON 형식이어야 합니다."})
            
            # 기존 메타데이터가 있는지 확인
            metadata_obj = article.article_metadata_set.first()
            
            if metadata_obj:
                if metadata:  # 비어있지 않으면 업데이트
                    metadata_obj.metadata = metadata
                    metadata_obj.save()
            elif metadata:  # 기존에 없고 새로 추가하는 경우
                ArticleMetadata.objects.create(
                    article=article,
                    metadata=metadata
                )
        
        return article
