# coding=utf-8
from django.conf.urls import url, patterns

urlpatterns = patterns('securestore.views',
					   url(r'^notfound/$', 'notfound', name='secure-404'),
						url(r'(?P<path>.*)', 'serve_secure_file', name='sercurestore_download'),
)
