from rest_framework import serializers

from apps.meal.models import Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="restaurant_name")

    class Meta:
        model = Restaurant
        fields = ["id", "code", "name"]
