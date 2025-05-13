from ara import redis

from rest_framework import decorators
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response

import datetime
import re

#쿼리로 들어온 날짜 형식 검사

def is_valid_date(pk):
    """
    pk가 YYYY-MM-DD 형식에 맞는지 확인하는 함수
    :param pk: 문자열로 된 날짜 (예: '2025-04-01')
    :return: True (유효한 형식), False (유효하지 않은 형식)
    """
    # 정규 표현식으로 YYYY-MM-DD 형식 확인
    pattern = r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"
    return bool(re.match(pattern, pk))


class MealViewSet(ViewSet):
    #허용된 method 지정
    http_method_names = ["get"]

    #목록 조회 요청 : 거절
    def list(self, request):
        return Response({"error": "이 API는 지원되지 않습니다."}, status=405)

    def retrieve(self, request, pk=None):
        return Response({"error": "이 API는 지원되지 않습니다."}, status=405)
    """
        특정 날짜의 식단을 조회하는 API
        :param request: 요청 객체
        :param pk: 날짜 (YYYY-MM-DD 형식)
        :return: 식단 정보
        api/meals/<date>/cafeteria_menu
        api/meals/<date>/course_menu
    """
    @decorators.action(detail=True, methods=["get"])
    def cafeteria_menu(self, request, pk=None):
        #형식 검사
        if not is_valid_date(pk):
            return Response({"error": "날짜 형식이 잘못되었습니다."}, status=400)

        # Redis에서 데이터 가져오기
        meal_data_cafeteria = redis.json().get('cafeteria_menu' + pk.replace("-", ""))

        if meal_data_cafeteria is None:
            return Response({"error": "식단 정보를 찾을 수 없습니다."}, status=404)

        return Response(meal_data_cafeteria)
    
    @decorators.action(detail=True, methods=["get"])
    def course_menu(self, request, pk=None):
        #형식 검사
        if not is_valid_date(pk):
            return Response({"error": "날짜 형식이 잘못되었습니다."}, status=400)

        # Redis에서 데이터 가져오기
        meal_data_course = redis.json().get('course_menu' + pk.replace("-", ""))

        if meal_data_course is None:
            return Response({"error": "식단 정보를 찾을 수 없습니다."}, status=404)

        return Response(meal_data_course)