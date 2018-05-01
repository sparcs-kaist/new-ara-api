from rest_framework import routers

from apps.core.views.viewsets import *


router = routers.SimpleRouter()


# BoardViewSet

router.register(
    prefix=r'boards',
    viewset=BoardViewSet,
)

# ArticleViewSet

router.register(
    prefix=r'articles',
    viewset=ArticleViewSet,
)

# CommentViewSet

router.register(
    prefix=r'comments',
    viewset=CommentViewSet,
)

# ReportViewSet

router.register(
    prefix=r'reports',
    viewset=ReportViewSet,
)

# BlockViewSet

router.register(
    prefix=r'blocks',
    viewset=BlockViewSet,
)

# AttachmentViewSet

router.register(
    prefix=r'attachments',
    viewset=AttachmentViewSet,
)

# ScrapViewSet

router.register(
    prefix=r'scraps',
    viewset=ScrapViewSet,
)

# NotificationViewSet

router.register(
    prefix=r'notifications',
    viewset=NotificationViewSet,
)
