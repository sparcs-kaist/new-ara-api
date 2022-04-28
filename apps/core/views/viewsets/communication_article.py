from django.utils.translation import gettext
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters, viewsets, response, permissions

from apps.core.models import Article
from apps.core.permissions.communication_article import CommunicationArticleAdminPermission
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models.communication_article import CommunicationArticle, SchoolResponseStatus
from apps.core.serializers.communication_article import BaseCommunicationArticleSerializer, \
    CommunicationArticleUpdateActionSerializer, CommunicationArticleSerializer


class CommunicationArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = CommunicationArticle.objects.all()
    serializer_class = BaseCommunicationArticleSerializer
    action_serializer_class = {
        'update': CommunicationArticleUpdateActionSerializer,
        'list': CommunicationArticleSerializer,
    }
    permission_classes = (
        permissions.IsAuthenticated,
        CommunicationArticleAdminPermission,
    )
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]

    # usage: /api/communication_articles/?ordering=created_at
    ordering_fields = ['article__positive_vote_count']
    ordering = ['-article__positive_vote_count']  # default: 추천수 내림차순

    # usage: /api/communication_articles/?school_response_status=1
    filterset_fields = ['school_response_status']

    # 학교 담당자가 신문고 게시글에 대해 `확인했습니다` 버튼을 누른 경우
    def update(self, request, *args, **kwargs):
        # user가 학교 담당자인지 확인
        if self.get_object().confirmed_by_school_at != timezone.datetime.min.replace(tzinfo=timezone.utc):
            return response.Response(status=status.HTTP_200_OK)
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save(
            confirmed_by_school_at=timezone.now(),
            school_response_status=SchoolResponseStatus.PREPARING_ANSWER,
        )
        return super().perform_update(serializer)
