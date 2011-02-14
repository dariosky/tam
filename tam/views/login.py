from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout_then_login as django_logout

from markViews import public
from tam.models import logAction

@public
def login(request):
	logged = request.user.is_authenticated() and request.user.username
	response = django_login(request, template_name="login.html")
	if request.user.is_authenticated() and request.user.username!=logged:	# just logged in
		log = logAction('L', instance=request.user, description='Accesso effettuato', user=request.user)
	return response

@public
def logout(request):
	logged = request.user.is_authenticated() and request.user
	response = django_logout(request, login_url="/")
	if not request.user.is_authenticated() and logged:	# just logged out
		log = logAction('O', instance=logged, description='Disconnesso', user=logged)
	return response
