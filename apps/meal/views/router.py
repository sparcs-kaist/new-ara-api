from rest_framework import routers
from apps.meal.views import viewsets

router = routers.DefaultRouter()

# 카페테리아 메뉴 관련 ViewSet
router.register(
    prefix=r"meal/cafeteria-menu",
    viewset=viewsets.CafeteriaMenuViewSet,
    basename="cafeteria_menu"
)

# 코스 관련 ViewSet
router.register(
    prefix=r"meal/course",
    viewset=viewsets.CourseViewSet,
    basename="course"
)

# 일반 메뉴 관련 ViewSet
router.register(
    prefix=r"meal/menu",
    viewset=viewsets.MenuViewSet,
    basename="menu"
)

# 메뉴 알러지 관련 ViewSet
router.register(
    prefix=r"meal/menu-allergy",
    viewset=viewsets.MenuAllergyViewSet,
    basename="menu_allergy"
)
