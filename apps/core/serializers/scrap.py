from django.db import IntegrityError
from django.utils.translation import gettext
from rest_framework import serializers

from apps.core.models import Scrap
from apps.core.serializers.article import ArticleListActionSerializer
from apps.core.serializers.mixins.scoped_board import ScopedBoardHiddenInfoMixin
from apps.course.access import deny_unenrolled_course_access, is_course_article
from apps.major.access import deny_non_same_major_access, is_major_article
from ara.classes.serializers import MetaDataModelSerializer


class BaseScrapSerializer(MetaDataModelSerializer):
    class Meta:
        model = Scrap
        fields = "__all__"


class ScrapParentArticleSerializer(
    ScopedBoardHiddenInfoMixin, ArticleListActionSerializer
):
    """스크랩 목록의 parent_article.

    스크랩 목록은 scoped viewset 의 권한 검사를 거치지 않으므로,
    `ScopedBoardHiddenInfoMixin` 을 그대로 태우면 접근권이 없는 scoped 글까지
    열려 버린다. 스크랩 생성 가드(`ScrapViewSet.create`)와 같은 헬퍼로 현재
    접근권을 확인해, 통과할 때만 mixin 의 보정을 태운다.
    """

    def _has_scoped_access(self, obj) -> bool:
        # hidden_info 는 필드마다 호출되므로 enrollment 조회를 글당 한 번으로 묶는다.
        cache = self.context.setdefault("_scrap_scoped_access", {})
        if obj.id not in cache:
            user = self.context["request"].user
            cache[obj.id] = (
                is_course_article(obj) or is_major_article(obj)
            ) and not (
                deny_unenrolled_course_access(user, obj)
                or deny_non_same_major_access(user, obj)
            )
        return cache[obj.id]

    def hidden_info(self, obj) -> tuple[bool, bool, list]:
        if self._has_scoped_access(obj):
            return super().hidden_info(obj)
        return ArticleListActionSerializer.hidden_info(self, obj)


class ScrapSerializer(BaseScrapSerializer):
    parent_article = ScrapParentArticleSerializer(
        read_only=True,
    )

    from apps.user.serializers.user import PublicUserSerializer

    scrapped_by = PublicUserSerializer(
        read_only=True,
    )


class ScrapCreateActionSerializer(MetaDataModelSerializer):
    class Meta(BaseScrapSerializer.Meta):
        read_only_fields = ("scrapped_by",)

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                gettext("This article is already scrapped.")
            )
