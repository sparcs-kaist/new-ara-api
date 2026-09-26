from django.db import models
from ara.db.models import MetaDataModel

"""
식당 이름 (말머리 처럼 수동 추가)
(id, name)
(1, "카이마루")
(2, "서맛골")
(3, "동맛골 1층")
(4, "동맛골 2층")
(5, "교수회관")
"""

class Restaurant(MetaDataModel):
    restaurant_name = models.CharField(
        verbose_name="식당 이름",
        max_length=32,
        unique=True,
    )
    # 학교 식단 페이지의 dvs_cd (fclt, west, east1 ...). 크롤러는 이름이 아니라 이 값으로 식당을 찾는다
    code = models.CharField(
        verbose_name="학교 사이트 코드",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        default=None,
    )
    # 없어진 식당은 지우지 않고 끈다 (과거 식단이 참조하므로)
    is_active = models.BooleanField(
        verbose_name="운영 중",
        default=True,
    )

    def __str__(self):
        return self.restaurant_name