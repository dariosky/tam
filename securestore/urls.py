from django.conf.urls import url, patterns, include
from django.conf import settings
import os

#urlpatterns = patterns('',
#	url(r'^$', "django.views.generic.simple.direct_to_template", {'template':'main.html'}, name="main" ),
#)

urlpatterns = patterns('securestore.views',
                       url(r'(?P<path>.*)', 'serve_secure_file', name='sercurestore_download')
)

#url(r'archivio/(?P<id_fattura>\d*)/$', 'fattura', name='tamFatturaId'),
