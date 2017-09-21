from rest_framework import routers

from apps.core.views.viewsets import *


router = routers.SimpleRouter()


# VoteViewSet

router.register(
    prefix=r'votes',
    viewset=VoteViewSet,
)


# ArticleViewSet

router.register(
    prefix=r'articles',
    viewset=ArticleViewSet,
)
