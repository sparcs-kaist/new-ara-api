from rest_framework import serializers
from ..models import Course, Menu, CafeteriaMenu

class BaseMenuSerializer(serializers.ModelSerializer):
    """알러지 코드 추출 및 경고 플래그 표시 여부 결정"""
    allergy_codes = serializers.SerializerMethodField()
    has_user_allergy = serializers.SerializerMethodField() 

    def get_allergy_codes(self, obj):
        return list(obj.allergy_set.values_list('allergen_code', flat=True))

    def get_has_user_allergy(self, obj):
        user_allergies = self.context.get('user_allergies', [])
        if not user_allergies:
            return False
        menu_allergies = set(obj.allergy_set.values_list('allergen_code', flat=True))
        return bool(menu_allergies.intersection(set(user_allergies)))

class MenuSerializer(BaseMenuSerializer):
    class Meta:
        model = Menu
        fields = ('menu_name', 'allergy_codes', 'has_user_allergy')

class CafeteriaMenuSerializer(BaseMenuSerializer):
    class Meta:
        model = CafeteriaMenu
        fields = ('menu_name', 'price', 'allergy_codes', 'has_user_allergy')

class CourseSerializer(serializers.ModelSerializer):
    menus = MenuSerializer(source='filtered_menus', many=True, read_only=True)
    class Meta:
        model = Course
        fields = ('restaurant_name', 'price', 'menus')

class DailyMealResponseSerializer(serializers.Serializer):
    courses = CourseSerializer(many=True)
    cafeteria_menus = CafeteriaMenuSerializer(many=True)