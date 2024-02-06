import typing

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import FCMToken, FCMTopic
from ara.firebase import fcm_subscrible, fcm_unsubscrible


class FCMTokenView(APIView):
    def patch(self, request, mode):
        token = request.data["token"]
        if mode == "delete":
            FCMToken.objects.filter(token=token).delete()
        elif mode == "update":
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            token = FCMToken(
                token=token, user=request.user, last_activated_at=timezone.now()
            )
            token.save()
        return Response(status=status.HTTP_200_OK)


class FCMTopicView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_topics = (
            FCMTopic.objects.filter(user=request.user)
            .values_list("topic", flat=True)
            .distinct()
        )
        return Response(user_topics)

    def patch(self, request):
        topic_put_list: typing.List[str] = request.data.get("put")
        topic_delete_list: typing.List[str] = request.data.get("delete")
        # TODO: sanitize user topic list to available topics
        user_id = str(request.user.id)

        user_tokens = list(
            FCMToken.objects.filter(user=request.user)
            .values_list("token", flat=True)
            .distinct()
        )
        fcm_subscrible(user_tokens, topic_put_list)
        for tpc in topic_put_list:
            FCMTopic.objects.get_or_create(user=request.user, topic=tpc)
        fcm_unsubscrible(user_tokens, topic_delete_list)
        for tpc in topic_delete_list:
            FCMTopic.objects.filter(user=request.user, topic=tpc).delete()

        return Response(status=status.HTTP_200_OK)
