from rest_framework import routers

router = routers.DefaultRouter()

router.register(
    prefix=r"notice",
)
