from django.conf.urls import url, include
from apps.session import views


urlpatterns = [
    url(r'^$', views.home),
    url(r'^login/$', views.user_login),
    url(r'^login/callback/$', views.login_callback),
    url(r'^logout/$', views.user_logout),
    url(r'^unregister/$', views.unregister),
]

