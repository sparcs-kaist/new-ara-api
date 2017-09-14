from rest_framework import routers

from apps.core.views.viewsets import *


router = routers.SimpleRouter()


# ArticleViewSet

router.register(
    prefix=r'articles',
    viewset=ArticleViewSet,
)
