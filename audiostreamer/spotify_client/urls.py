from django.conf.urls import url

from spotify_client import views

urlpatterns = [
    url(r'^$', views.index, name='index')
]