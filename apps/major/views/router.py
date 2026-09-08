from rest_framework import routers

from apps.major.views.viewsets.article import MajorArticleViewSet
from apps.major.views.viewsets.major import MajorViewSet

router = routers.DefaultRouter()

# MajorViewSet
# list 외에 my-major / user_major_add / user_major_remove 는 viewset 의
# @action 이 라우트를 만든다.
router.register(
    prefix=r"majors",
    viewset=MajorViewSet,
    basename="major",
)

# MajorArticleViewSet
# 학과 하위 중첩 라우트. prefix 의 named group 이 그대로 viewset 의
# self.kwargs["std_dept_id"] 로 들어간다.
router.register(
    prefix=r"majors/(?P<std_dept_id>[0-9]+)/articles",
    viewset=MajorArticleViewSet,
    basename="major-article",
)
