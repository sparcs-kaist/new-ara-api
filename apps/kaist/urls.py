from django.urls import path
from .views.trending_posts import TrendingPostsView

urlpatterns = [
    path("trending/", TrendingPostsView.as_view(), name="trending_posts"),
]