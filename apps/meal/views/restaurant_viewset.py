from rest_framework import mixins, permissions

from ara.classes.viewset import ActionAPIViewSet
from apps.meal.models import Restaurant
from apps.meal.serializers.restaurant_serializers import RestaurantSerializer


class RestaurantViewSet(mixins.ListModelMixin, ActionAPIViewSet):
    queryset = Restaurant.objects.filter(is_active=True).order_by("id")
    serializer_class = RestaurantSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
