""" Each request needs an authenticathed user """
from django.contrib.auth.decorators import login_required

class RequireLoginMiddleware(object):
	"""Middleware that gets various objects from the
	request object and saves them in thread local storage."""
	def process_view(self, request, view_func, view_args, view_kwargs):
		public_view = getattr(view_func, 'public', False)
		if public_view or view_func.func_name=="serve":
#			logging.debug("Public view")
			return None
		else:
#			logging.debug("Login view %s", view_func)
			return login_required(view_func)(request,*view_args,**view_kwargs)
