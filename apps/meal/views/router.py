from rest_framework import routers
from apps.meal.views import meal_viewset

router = routers.DefaultRouter()

router.register(
    prefix=r"meal",
    viewset=meal_viewset.MealViewSet,
    basename="meal",
)