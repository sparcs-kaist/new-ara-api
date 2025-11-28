from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Prefetch
from datetime import date as date_type
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from ..models import Course, Menu, CafeteriaMenu
from ..serializers.meal_serializers import CourseSerializer, CafeteriaMenuSerializer

class MealViewSet(viewsets.ViewSet):

    @extend_schema(
        summary="식단 조회",
        description="특정 날짜, 식당, 시간대의 식단 정보를 조회합니다.",
        parameters=[
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='조회할 날짜 (YYYYMMDD 형식, 예: 20251128)',
                required=True,
            ),
            OpenApiParameter(
                name='restaurant_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='식당 ID (1: 카이마루, 2: 서맛골, 3: 동맛골 1층, 4: 동맛골 2층, 5: 교수회관)',
                required=True,
            ),
            OpenApiParameter(
                name='meal_time',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='식사 시간대 (BREAKFAST, LUNCH, DINNER)',
                required=True,
                enum=['BREAKFAST', 'LUNCH', 'DINNER'],
            ),
            OpenApiParameter(
                name='allergy_codes',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='필터링할 알러지 코드 (쉼표로 구분, 예: 1,5,6)',
                required=False,
            ),
        ],
    )
    def list(self, request):
        date_str = request.query_params.get('date') 
        restaurant_id = request.query_params.get('restaurant_id')
        meal_time = request.query_params.get('meal_time')
        
        if not all([date_str, restaurant_id, meal_time]):
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            query_date = date_type(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
        except (ValueError, TypeError):
             return Response({'error': 'Invalid date'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            restaurant_id = int(restaurant_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid restaurant_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        """알러지 필터 context 생성"""
        raw_codes = request.query_params.get('allergy_codes', '')
        user_allergies = [int(c.strip()) for c in raw_codes.split(',') if c.strip()]
        context = {'user_allergies': user_allergies}
        
        """일반 코스 메뉴 조회"""
        all_menus_qs = Menu.objects.all().prefetch_related('allergy_set')
        
        course_queryset = Course.objects.filter(
            restaurant_id=restaurant_id, 
            date=query_date,
            meal_time=meal_time
        ).prefetch_related(
            Prefetch('menu_set', queryset=all_menus_qs, to_attr='filtered_menus') 
        )
        
        course_serializer = CourseSerializer(course_queryset, many=True, context=context)
        
        """카페테리아 메뉴 조회"""
        cafeteria_queryset = CafeteriaMenu.objects.filter(
            restaurant_id=restaurant_id,
            date=query_date,
            meal_time=meal_time,
        ).prefetch_related('allergy_set')

        cafeteria_serializer = CafeteriaMenuSerializer(cafeteria_queryset, many=True, context=context)


        return Response({
            'restaurant_id': restaurant_id,
            'courses': course_serializer.data,
            'cafeteria_menus': cafeteria_serializer.data,
        }, status=status.HTTP_200_OK)