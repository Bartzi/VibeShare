from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'audiostreamer.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r"^$", 'webui.views.index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^smb/', include('musicfinder.urls')),
    url(r'^webui/', include('webui.urls')),
    url(r'^spotify/', include('spotify_client.urls')),
)
