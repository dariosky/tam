# coding=utf-8
""" Each request needs an authenticathed user """
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist


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
			except ObjectDoesNotExist:
				prenotazioni_user = False

			if prenotazioni_user and not prenotazioni_view:
				#messages.error(request, "Gli utenti del servizio prenotazioni non hanno accesso a questa pagina.")
				return HttpResponseRedirect(reverse('tamPrenotazioni'))

			elif not prenotazioni_user and prenotazioni_view:
				#messages.error(request, "I conducenti non possono accedere alle prenotazioni.")
				return HttpResponseRedirect(reverse('tamCorse'))
			else:
				if request.user.is_authenticated():
					# everything is OK proceed with other middlewares
					return None
				else:
					# we are not logged in so let login_required redirect us
					return login_required(view_func)(request, *view_args, **view_kwargs)


def csrf_failure_view(request, reason=''):
	return render_to_response('403.html', {}, context_instance=RequestContext(request))
