from django.utils.translation import gettext
from rest_framework import mixins, response, status

from apps.core.documents import ArticleDocument
from apps.core.models import Article, ArticleReadLog, Scrap
from apps.core.permissions.scrap import ScrapPermission
from apps.core.serializers.scrap import ScrapCreateActionSerializer, ScrapSerializer
from apps.course.access import deny_unenrolled_course_access
from apps.major.access import deny_non_same_major_access
from ara.classes.viewset import ActionAPIViewSet


class ScrapViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Scrap.objects.all()
    serializer_class = ScrapSerializer
    action_serializer_class = {
        "create": ScrapCreateActionSerializer,
    }
    permission_classes = (ScrapPermission,)

    def get_queryset(self):
        queryset = super(ScrapViewSet, self).get_queryset()

        queryset = queryset.filter(scrapped_by=self.request.user)

        search_keyword = self.request.query_params.get("main_search__contains")
        if search_keyword:
            queryset = queryset.filter(
                id__in=ArticleDocument.get_main_search_id_set(search_keyword)
            )

        queryset = queryset.select_related(
            "scrapped_by",
            "scrapped_by__profile",
            "parent_article",
            "parent_article__created_by",
            "parent_article__created_by__profile",
            "parent_article__parent_topic",
            "parent_article__parent_board",
        ).prefetch_related(
            "parent_article__attachments",
            ArticleReadLog.prefetch_my_article_read_log(
                self.request.user, prefix="parent_article__"
            ),
        )

        return queryset

    def create(self, request, *args, **kwargs):
        # Defense in depth: scoped article은 enrollment 또는 same-major를 검사한다.
        # Missing article validation은 serializer에 위임해 기존 `400` response를 유지한다.
        parent_article_id = request.data.get("parent_article")
        if parent_article_id:
            article = Article.objects.filter(pk=parent_article_id).first()
            if article is not None and (
                deny_unenrolled_course_access(request.user, article)
                or deny_non_same_major_access(request.user, article)
            ):
                return response.Response(
                    {"message": gettext("해당 게시판에 접근할 권한이 없습니다.")},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )
