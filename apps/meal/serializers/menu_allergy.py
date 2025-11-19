from rest_framework import serializers
from meal.models import MenuAllergy

class MenuAllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuAllergy
        fields = "__all__"
