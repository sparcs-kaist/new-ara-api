from django.db.models.functions import Now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import FCMToken, FCMTopic
from ara.firebase import fcm_subscrible, fcm_unsubscrible


class FCMTokenView(APIView):
    def patch(self, request, mode):
        token = request.data["token"]
        if mode == "delete":
            FCMToken.objects.filter(token=token).delete()
            pass
        elif mode == "update":
            if not request.user.is_authenticated:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
            token = FCMToken(token=token, user=request.user, last_activated_at=Now())
            token.save()
        return Response(status=status.HTTP_200_OK)


class FCMTopicView(APIView):
    def get(self, request):
        # TODO: More better way for authentication guard?
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # user_topics = tmp_topic_storage.get(str(request.user.id))
        user_topics = (
            FCMTopic.objects.filter(user=request.user)
            .values_list("topic", flat=True)
            .distinct()
        )
        return Response(user_topics)

    def patch(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        topic_put_list: list[str] = request.data.get("put")
        topic_delete_list: list[str] = request.data.get("delete")
        # print(topic_put_list, topic_delete_list)
        # TODO: santize user topic list to available topics
        user_id = str(request.user.id)

        # tmp_topic_storage = {
        #     '1': set(['board_13', 'board_17', 'portal_popular', 'article_8148']),
        # }
        # if tmp_topic_storage.get(user_id) == None:
        #     tmp_topic_storage[user_id] = set()
        # user_topics = tmp_topic_storage[user_id]
        # user_topics.update(topic_put_list)
        # user_topics.difference_update(topic_delete_list)

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
