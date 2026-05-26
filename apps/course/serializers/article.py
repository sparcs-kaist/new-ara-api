"""과목게시판용 Article serializer.

기존 apps.core 의 Article serializer 와 분리해서 과목게시판 도메인의
간소한 응답만 다룬다 (block/scrap/vote 등 일반 board 부가기능 제외).
모든 글은 익명 (name_type=ANONYMOUS) 강제.
"""

from rest_framework import serializers

from apps.core.models import Article
from apps.core.models.board import NameType


class CourseArticleListSerializer(serializers.ModelSerializer):
    """목록 응답: 본문 일부, 댓글 수, 투표 수 정도만."""

    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "created_at",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "hit_count",
        )
        read_only_fields = fields


class CourseArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = (
            "id",
            "title",
            "content",
            "content_text",
            "created_at",
            "content_updated_at",
            "comment_count",
            "positive_vote_count",
            "negative_vote_count",
            "hit_count",
        )
        read_only_fields = fields


class CourseArticleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "content", "content_text")

    def create(self, validated_data):
        # 과목게시판 글은 익명 + 부모 board 강제 주입.
        # 게시판 묶음은 related_course_group (학기 무관), related_course 는 출처용.
        # 호출 viewset 에서 context["course"], context["course_group"],
        # context["board_id"] 주입.
        course = self.context["course"]
        course_group = self.context["course_group"]
        board_id = self.context["board_id"]
        return Article.objects.create(
            **validated_data,
            parent_board_id=board_id,
            related_course=course,
            related_course_group=course_group,
            name_type=NameType.ANONYMOUS.value,
            created_by=self.context["request"].user,
        )


class CourseArticleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ("title", "content", "content_text")
