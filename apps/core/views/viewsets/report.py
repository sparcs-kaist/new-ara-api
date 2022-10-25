from django.utils.translation import gettext
from rest_framework import mixins
from django.core.mail import send_mail
from apps.core.models import Article, Comment
from ara.classes.viewset import ActionAPIViewSet
from rest_framework import status
from rest_framework.response import Response

from apps.core.models import (
    ArticleReadLog,
    Block,
    Report,
)
from apps.core.permissions.report import ReportPermission
from apps.core.serializers.report import (
    ReportSerializer,
    ReportCreateActionSerializer,
)
from ara.settings import env


class ReportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    ActionAPIViewSet,
):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    action_serializer_class = {
        "create": ReportCreateActionSerializer,
    }
    permission_classes = (ReportPermission,)

    def get_queryset(self):
        queryset = super(ReportViewSet, self).get_queryset()

        queryset = (
            queryset.filter(
                reported_by=self.request.user,
            )
            .select_related(
                "reported_by",
                "reported_by__profile",
                "parent_article",
                "parent_article__created_by",
                "parent_article__created_by__profile",
                "parent_article__parent_topic",
                "parent_article__parent_board",
                "parent_comment",
                "parent_comment__created_by",
                "parent_comment__created_by__profile",
            )
            .prefetch_related(
                "parent_article__attachments",
                ArticleReadLog.prefetch_my_article_read_log(
                    self.request.user, prefix="parent_article__"
                ),
            )
        )

        return queryset

    @staticmethod
    def send_email_for_article_report(request):
        django_env = "PROD" if env("DJANGO_ENV") == "production" else "DEV"
        article_link = (
            "newara.sparcs.org"
            if env("DJANGO_ENV") == "production"
            else "newara.dev.sparcs.org"
        )

        parent_article_id = request.data.get("parent_article")
        parent_comment_id = request.data.get("parent_comment")

        if parent_article_id:
            parent_id = parent_article_id
            parent = Article.objects.get(id=parent_article_id)
            report_type = "Article"
            parent_title = parent.title
            parent_content = parent.content_text
        else:
            parent_id = parent_comment_id
            parent = Comment.objects.get(id=parent_comment_id)
            parent_article_id = parent.get_parent_article()
            report_type = "Comment"
            parent_title = "None"
            parent_content = parent.content

        title = f"[{django_env} 신고 ({report_type})] '{request.user.id}:: {request.user.profile}'님께서 {report_type} {parent_id}을 신고하였습니다."
        message = (
            f"{report_type} {parent_id}에 대하여 다음과 같은 신고가 접수되었습니다:\n"
            f"게시글 바로가기: {article_link}/post/{parent_article_id}\n"
            f"신고자: {request.user.id}:: {request.user.profile}\n"
            f"신고 유형: {request.data.get('type')}\n"
            f"신고 사유: {request.data.get('content')}\n"
            f"글 종류: {report_type}\n"
            f"작성자: {parent.created_by.id}:: {parent.created_by.profile}\n"
            f"제목: {parent_title}\n"
            f"내용: {parent_content}\n"
        )

        send_mail(title, message, "new-ara@sparcs.org", ["new-ara@sparcs.org"])

    def perform_create(self, serializer):
        serializer.save(
            reported_by=self.request.user,
        )

    def create(self, request, *args, **kwargs):
        parent_article_id = request.data.get("parent_article")
        parent_comment_id = request.data.get("parent_comment")

        if parent_article_id:
            parent_article = Article.objects.filter(id=parent_article_id).first()
            if not parent_article or parent_article.is_hidden_by_reported():
                return Response(
                    {
                        "message": gettext(
                            "Cannot report articles that are deleted or hidden by reports"
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif parent_comment_id:
            parent_comment = Comment.objects.filter(id=parent_comment_id).first()
            if (
                not parent_comment
                or parent_comment.is_deleted()
                or parent_comment.is_hidden_by_reported()
            ):
                return Response(
                    {
                        "message": gettext(
                            "Cannot report comments that are deleted or hidden by reports"
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            self.send_email_for_article_report(request)

        return response
