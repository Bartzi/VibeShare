from django.conf.urls import url

from webui import views

urlpatterns = [
    url(r'^$', views.index, name='index')
]