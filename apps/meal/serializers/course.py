from rest_framework import serializers
from meal.models import Course
from .menu_serializer import MenuSerializer

class CourseSerializer(serializers.ModelSerializer):
    menu_set = MenuSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
