from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Prefetch
from datetime import date as date_type
from ..models import Course, Menu, CafeteriaMenu
from ..serializers.meal_serializers import CourseSerializer, CafeteriaMenuSerializer

class MealViewSet(viewsets.ViewSet):

    def list(self, request):
        date_str = request.query_params.get('date') 
        restaurant_name = request.query_params.get('restaurant_name')
        meal_time = request.query_params.get('meal_time')
        
        if not all([date_str, restaurant_name, meal_time]):
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query_date = date_type(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
        except (ValueError, TypeError):
             return Response({'error': 'Invalid date'}, status=status.HTTP_400_BAD_REQUEST)

        """알러지 필터 context 생성"""
        raw_codes = request.query_params.get('allergy_codes', '')
        user_allergies = [int(c.strip()) for c in raw_codes.split(',') if c.strip()]
        context = {'user_allergies': user_allergies}
        
        """일반 코스 메뉴 조회"""
        all_menus_qs = Menu.objects.all().prefetch_related('allergy_set')
        
        course_queryset = Course.objects.filter(
            restaurant_id__restaurant_name=restaurant_name, 
            date=query_date,
            meal_time=meal_time
        ).prefetch_related(
            Prefetch('menu_set', queryset=all_menus_qs, to_attr='filtered_menus') 
        )
        
        course_serializer = CourseSerializer(course_queryset, many=True, context=context)
        
        """카페테리아 메뉴 조회"""
        cafeteria_queryset = CafeteriaMenu.objects.filter(
            restaurant_id__restaurant_name=restaurant_name,
            date=query_date,
            meal_time=meal_time,
        ).prefetch_related('allergy_set')

        cafeteria_serializer = CafeteriaMenuSerializer(cafeteria_queryset, many=True, context=context)


        return Response({
            'restaurant': restaurant_name,
            'courses': course_serializer.data,
            'cafeteria_menus': cafeteria_serializer.data,
        }, status=status.HTTP_200_OK)