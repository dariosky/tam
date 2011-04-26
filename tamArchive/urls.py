from django.conf.urls.defaults import *

urlpatterns = patterns('tamArchive.archiveViews',
    url(r'^panel/$', 'menu', name='tamArchiveUtil'),
	url(r'^doArchive/$', 'action', name='tamArchiveAction'),
	url(r'^flat/$', 'flat', name='tamArchiveFlat'),
	url(r'^view/$', 'view', name='tamArchiveView'),
)
