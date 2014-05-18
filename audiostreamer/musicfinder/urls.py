from django.conf.urls import url

from musicfinder import views

urlpatterns = [
    url(r'^$', views.discover_music, name='discover')
]