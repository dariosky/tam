from django.conf.urls import url, patterns

urlpatterns = patterns('codapresenze.views',
                       url(r'', 'coda', name='codapresenze-home'),  #url(r'socket\.io', 'socketio')

)
