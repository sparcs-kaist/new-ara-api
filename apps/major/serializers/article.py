"""과목게시판용 Article serializer.

기존 apps.core 의 Article serializer 와 분리해서 과목게시판 도메인의
간소한 응답만 다룬다 (block/scrap/vote 등 일반 board 부가기능 제외).
모든 글은 익명 (name_type=ANONYMOUS) 강제.
"""

from apps.user.serializers.user import PublicUserSerializer
from rest_framework import serializers

from apps.core.models import Article
from apps.core.models.board import NameType


class MajorArticleListSerializer(serializers.ModelSerializer):
    """목록 응답: 본문 일부, 댓글 수, 투표 수 정도만."""
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "created_at",
            "created_by",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "hit_count",
        )
        read_only_fields = fields

    def get_created_by(self, obj):
        return PublicUserSerializer(obj.postprocessed_created_by).data


class MajorArticleSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "content_text",
            "created_at",
            "created_by",
            "content_updated_at",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "hit_count",
        )
        read_only_fields = fields
    def get_created_by(self, obj):
        return PublicUserSerializer(obj.postprocessed_created_by).data


class MajorArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "content", "content_text")

    def create(self, validated_data):
        # 학과게시판 글은 익명 + 부모 board / related_major 강제 주입.
        # 호출 viewset 에서 context["major"], context["board_id"] 주입.
        major = self.context["major"]
        board_id = self.context["board_id"]
        return Article.objects.create(
            **validated_data,
            parent_board_id=board_id,
            related_major=major,
            name_type=NameType.REGULAR.value,
            created_by=self.context["request"].user,
        )


class MajorArticleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "content", "content_text")
