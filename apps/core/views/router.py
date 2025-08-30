from rest_framework import routers

from apps.core.views import viewsets

router = routers.DefaultRouter()

# BoardViewSet
router.register(
    prefix=r"boards",
    viewset=viewsets.BoardViewSet,
)

router.register(
    prefix=r"board_groups",
    viewset=viewsets.BoardGroupViewSet,
)

# ArticleViewSet
router.register(
    prefix=r"articles",
    viewset=viewsets.ArticleViewSet,
)

# CommentViewSet
router.register(
    prefix=r"comments",
    viewset=viewsets.CommentViewSet,
)

# ReportViewSet
router.register(
    prefix=r"reports",
    viewset=viewsets.ReportViewSet,
)

# BlockViewSet
router.register(
    prefix=r"blocks",
    viewset=viewsets.BlockViewSet,
)

# AttachmentViewSet
router.register(
    prefix=r"attachments",
    viewset=viewsets.AttachmentViewSet,
)

# ScrapViewSet
router.register(
    prefix=r"scraps",
    viewset=viewsets.ScrapViewSet,
)

# NotificationViewSet
router.register(
    prefix=r"notifications",
    viewset=viewsets.NotificationViewSet,
)

# FAQViewSet
router.register(
    prefix=r"faqs",
    viewset=viewsets.FAQViewSet,
)

# BestSearchViewSet
router.register(
    prefix=r"best_searches",
    viewset=viewsets.BestSearchViewSet,
)

#meal : 학식 크롤링 기능
router.register(
    prefix=r"meals",
    viewset=viewsets.MealViewSet,
    #단순한 api여서 queryset을 사용하지 않았으므로 basename 설정.
    basename="meal",
)
