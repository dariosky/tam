""" Each request needs an authenticathed user """
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

class RequireLoginMiddleware(object):
	"""Middleware that gets various objects from the
	request object and saves them in thread local storage."""
	def process_view(self, request, view_func, view_args, view_kwargs):
		public_view = getattr(view_func, 'public', False)

		# public view or named "serve" <= (django.views.static.serve)
		if public_view or view_func.func_name == "serve":
			return None
		else:
			# not a public view, if not authenticaded ask for login
			if not request.user.is_authenticated():
				return login_required(view_func)(request, *view_args, **view_kwargs)
				
			prenotazioni_view = getattr(view_func, 'prenotazioni', False)
			try:
				prenotazioni_user = request.user.prenotazioni
			except:
				prenotazioni_user = False

			if prenotazioni_user and not prenotazioni_view:
				#messages.error(request, "Gli utenti del servizio prenotazioni non hanno accesso a questa pagina.")
				return HttpResponseRedirect(reverse('tamPrenotazioni'))

			elif not prenotazioni_user and prenotazioni_view:
				#messages.error(request, "I conducenti non possono accedere alle prenotazioni.")
				return HttpResponseRedirect(reverse('tamCorse'))
			else:
				return login_required(view_func)(request, *view_args, **view_kwargs)
