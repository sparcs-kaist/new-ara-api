from rest_framework import serializers
from meal.models import Menu
from .menu_allergy_serializer import MenuAllergySerializer

class MenuSerializer(serializers.ModelSerializer):
    allergy_set = MenuAllergySerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = "__all__"
