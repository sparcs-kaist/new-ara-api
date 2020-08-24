from django.urls import path, include

from apps.core.views import HomeView, StatusView, RecentView, router

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/home/', view=HomeView.as_view(), name='HomeView'),
    path('api/status/', view=StatusView.as_view(), name='StatusView'),
    path('api/recents/', view=RecentView.as_view(), name='RecentView'),
]
