from django.conf.urls import url, patterns

urlpatterns = patterns ('board.views',
	url(r'', 'main', name='board-home'),
	#url(r'socket\.io', 'socketio')

 )
