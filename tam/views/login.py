from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout_then_login as django_logout
from django.conf import settings
from django.http import HttpResponseServerError
from markViews import public
from modellog.actions import logAction

@public
def login(request):
	logged = request.user.is_authenticated() and request.user.username

	response = django_login(request,
							template_name="login.html",
							extra_context={	'logo_consorzio':settings.TRANSPARENT_LOGO,
											'nome_consorzio':settings.LICENSE_OWNER
										}
						)
	if request.user.is_authenticated() and request.user.username!=logged:	# just logged in
		logAction('L', description='Accesso effettuato', user=request.user)
	else:
		if request.is_ajax():
			return HttpResponseServerError("Please login")

	return response

@public
def logout(request):
	logged = request.user.is_authenticated() and request.user
	response = django_logout(request, login_url="/")
	if not request.user.is_authenticated() and logged:	# just logged out
		logAction('O', description='Disconnesso', user=logged)
	return response
