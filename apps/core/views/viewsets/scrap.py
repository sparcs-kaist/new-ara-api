from django.shortcuts import get_object_or_404
from django.utils.translation import gettext
from rest_framework import mixins, response, status

from apps.core.documents import ArticleDocument
from apps.core.models import Article, ArticleReadLog, Scrap
from apps.core.permissions.scrap import ScrapPermission
from apps.core.serializers.scrap import ScrapCreateActionSerializer, ScrapSerializer
from apps.course.access import can_read_article
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
        # 과목글 scrap 시 enrollment 가 없으면 403 (defense in depth: id 추측/유출 방지)
        parent_article_id = request.data.get("parent_article")
        if parent_article_id:
            article = get_object_or_404(Article, pk=parent_article_id)
            if not can_read_article(request.user, article):
                return response.Response(
                    {"message": gettext("해당 게시판에 접근할 권한이 없습니다.")},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(
            scrapped_by=self.request.user,
        )
