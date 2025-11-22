from rest_framework import routers
from apps.meal.views import meal_viewset

router = routers.DefaultRouter()

router.register(
    prefix=r"",
    viewset=meal_viewset.MealViewSet,
    basename="meal",
)