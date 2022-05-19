from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters, viewsets, response, permissions

from apps.core.permissions.communication_article import CommunicationArticleAdminPermission
from ara.classes.viewset import ActionAPIViewSet

from apps.core.models.communication_article import CommunicationArticle
from apps.core.serializers.communication_article import CommunicationArticleSerializer


class CommunicationArticleViewSet(viewsets.ModelViewSet, ActionAPIViewSet):
    queryset = CommunicationArticle.objects.all()
    serializer_class = CommunicationArticleSerializer
    action_serializer_class = {
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
