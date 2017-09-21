from django.db import transaction

from rest_framework import mixins

from ara.classes.viewset import ActionAPIViewSet

from apps.core.models import Vote
from apps.core.permissions.vote import VotePermission
from apps.core.serializers.vote import VoteCreateActionSerializer, VoteUpdateActionSerializer


class VoteViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, ActionAPIViewSet):
    queryset = Vote.objects.all()
    action_serializer_class = {
        'create': VoteCreateActionSerializer,
        'update': VoteUpdateActionSerializer,
        'partial_update': VoteUpdateActionSerializer,
    }
    permission_classes = (
        VotePermission,
    )

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save(
                created_by=self.request.user,
            )

            if instance.is_positive:
                instance.parent.positive_vote_count += 1

            else:
                instance.parent.negative_vote_count += 1

            instance.parent.save()

    def perform_update(self, serializer):
        with transaction.atomic():
            instance = serializer.instance

            if instance.is_positive:
                instance.parent.positive_vote_count -= 1

            else:
                instance.parent.negative_vote_count -= 1

            instance = serializer.save(
                created_by=self.request.user,
            )

            if instance.is_positive:
                instance.parent.positive_vote_count += 1

            else:
                instance.parent.negative_vote_count += 1

            instance.parent.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            if instance.is_positive:
                instance.parent.positive_vote_count -= 1

            else:
                instance.parent.negative_vote_count -= 1

            instance.delete()

            instance.parent.save()
