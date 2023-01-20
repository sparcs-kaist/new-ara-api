from django.db.models.functions import Now
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import FCMToken

# TODO: make model, and apply it
tmp_topic_storage = {
    '1': set(['board/13', 'board/17', 'portal/popular', 'article/8148']),
}

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
        # TODO: More better way?
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        user_topics = tmp_topic_storage.get(str(request.user.id))
        return Response(user_topics)

    def patch(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        topic_put_list: list[str] = request.data.get('put')
        topic_delete_list: list[str] = request.data.get('delete')
        user_id = str(request.user.id)

        if tmp_topic_storage.get(user_id) == None:
            tmp_topic_storage[user_id] = set()
        for topic in topic_put_list:
            print(topic, user_id)
            tmp_topic_storage[user_id].add(topic)

        user_topics = tmp_topic_storage.get(user_id)
        for topic in topic_delete_list:
            if user_topics and topic in user_topics:
                user_topics.remove(topic)
        

        return Response(status=status.HTTP_200_OK)
