from django.conf.urls.defaults import *
import settings

#urlpatterns = patterns('',
#    url(r'^$', "django.views.generic.simple.direct_to_template", {'template':'main.html'}, name="main" ),
#)

urlpatterns = patterns ( '',
	( r'^', include( 'tam.urls' ) ),
 )

from django.contrib import admin
admin.autodiscover()
urlpatterns += patterns('',
    ("^"+settings.MEDIA_URL[1:]+r'(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^admin/(.*)', admin.site.root),
)