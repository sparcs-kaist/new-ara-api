from rest_framework import serializers

from apps.meal.models import Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="restaurant_name")
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = ["id", "code", "name", "display_name", "is_active"]

    def get_display_name(self, obj):
        return obj.display_name or obj.restaurant_name
