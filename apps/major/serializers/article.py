"""학과게시판용 Article serializer.

읽기 serializer 는 core 의 ArticleSerializer / ArticleListActionSerializer 를
상속해서 hidden(신고 누적) · block(차단 유저) · 성인/정치 글 마스킹 파이프라인을
그대로 탄다. 필드는 Meta.fields 로 학과게시판에 필요한 것만 좁힌다.
(예전엔 평범한 ModelSerializer 라 title/content 를 마스킹 없이 그대로 노출했다.)

작성자 표기는 닉네임(REGULAR) — 익명 아님.
"""

from rest_framework import serializers

from apps.core.models import Article
from apps.core.models.board import NameType
from apps.core.serializers.article import (
    ArticleListActionSerializer,
    ArticleSerializer,
)
from apps.core.serializers.mixins.scoped_board import ScopedBoardHiddenInfoMixin


class MajorArticleListSerializer(
    ScopedBoardHiddenInfoMixin, ArticleListActionSerializer
):
    """목록 응답: 제목, 댓글 수, 투표 수 정도만."""

    class Meta:
        # 부모 Meta 를 상속하면 exclude 가 따라와 fields 와 충돌하므로 새로 정의한다.
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
            "is_hidden",
            "why_hidden",
            "can_override_hidden",
        )


class MajorArticleSerializer(ScopedBoardHiddenInfoMixin, ArticleSerializer):
    """상세 응답. content 는 마스킹 대상이라 SerializerMethodField 로 내려간다."""

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "created_at",
            "created_by",
            "content_updated_at",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "hit_count",
            "is_mine",
            "is_hidden",
            "why_hidden",
            "can_override_hidden",
        )


class MajorArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "content", "content_text")

    def create(self, validated_data):
        # 학과게시판 글은 닉네임(REGULAR) + 부모 board / related_major 강제 주입.
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
