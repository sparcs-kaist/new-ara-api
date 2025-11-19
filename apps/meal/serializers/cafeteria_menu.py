from rest_framework import serializers
from meal.models import CafeteriaMenu
from .menu_allergy_serializer import MenuAllergySerializer

class CafeteriaMenuSerializer(serializers.ModelSerializer):
    allergy_set = MenuAllergySerializer(many=True, read_only=True)

    class Meta:
        model = CafeteriaMenu
        fields = "__all__"
