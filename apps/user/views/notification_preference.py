from rest_framework import exceptions, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.models import UserNotificationPreference
from apps.user.serializers.notification_preference import UserNotificationPreferenceSerializer

DELIVERY_OFF_WARNING = (
    "함께 배달 알림을 끄면 마감, 확정, 도착 소식을 받지 못해요. "
    "알림을 못 받아 생긴 문제(배달 음식 분실, 정산 누락 등)는 책임지지 않아요."
)


class DeliveryOffConfirmRequired(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "confirm_required"


class NotificationPreferenceView(APIView):
    """
    내 푸시 알림 설정. 끄면 푸시만 안 가고 알림함에는 남는다
    함께 배달 소식을 끄려면 confirm_delivery_off: true 를 같이 보내야 한다
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        preference = UserNotificationPreference.get_for(request.user)
        return Response(UserNotificationPreferenceSerializer(preference).data)

    def patch(self, request):
        preference = UserNotificationPreference.get_for(request.user)
        serializer = UserNotificationPreferenceSerializer(preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        if preference.delivery and data.get("delivery") is False and not data.get("confirm_delivery_off"):
            raise DeliveryOffConfirmRequired({"detail": DELIVERY_OFF_WARNING, "code": "confirm_required"})

        serializer.save()
        return Response(serializer.data)
