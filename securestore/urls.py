from django.conf.urls import url, patterns

urlpatterns = patterns('securestore.views',
                       url(r'(?P<path>.*)', 'serve_secure_file', name='sercurestore_download')
)
