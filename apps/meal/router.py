from rest_framework import routers
from apps.meal.views import daily_meal_view

router = routers.DefaultRouter()

router.register(
    prefix=r"meal",
    viewset=daily_meal_view.MealViewSet,
    basename="meal",
)