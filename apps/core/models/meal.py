from ara.db.models import MetaDataModel
from django.db import models 

#Note : 이 파일이 아직 사용되는데 없음!!!!!
#크롤링한 학식 정보가 Main DB에 들어갈 것을 예상해서 만들었으나, Redis에만 넣기로 해서 더이상 쓸모가 없어짐.

class Meal(MetaDataModel):
    date = models.CharField(
        verbose_name="날짜",
        max_length=10,  # YYYY-MM-DD
    )
    restaurant = models.PositiveSmallIntegerField(
        verbose_name="식당 위치",
        db_index=True,
        choices=[
            (1, "카이마루"),
            (2, "서맛골"),
            (3, "동맛골 1층 카페테리아"),
            (4, "동맛골 1층"),
            (5, "동맛골 2층"),
            (6, "교수회관")
        ]
    )
    meal_time = models.PositiveSmallIntegerField(
        verbose_name="식사 시간 (아침 (1) /점심 (2) /저녁 (3))",
        db_index=True,
        choices=[
            (1, "조식"),
            (2, "중식"),
            (3, "석식")
        ]
    )
    type = models.CharField(
        verbose_name="식당 유형",
        max_length=10,
        choices=[
            ("cafeteria", "Cafeteria"),
            ("course", "Course"),
        ],
        #실제 api에서 카페테리아와 세트 메뉴를 구별할 일이 없기 때문에...
        db_index=False,
    )
    course_name = models.CharField(
        verbose_name="코스 이름",
        max_length=100,
        null=True,
        blank=True,
    )
    course_price = models.PositiveIntegerField(
        verbose_name="코스 가격",
        null=True,
        blank=True,
    )
    menu_list = models.JSONField(
        verbose_name="메뉴 리스트 (JSON)",
        null=True,
        blank=True,
    )

#db아니고 그냥 클래스임!
