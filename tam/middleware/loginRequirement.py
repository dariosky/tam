# coding=utf-8
""" Each request needs an authenticathed user """
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import mail_admins
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("tam.general")


class RequireLoginMiddleware(MiddlewareMixin):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""

    def process_view(self, request, view_func, view_args, view_kwargs):
        public_view = getattr(view_func, "public", False)

        # public view or named "serve" <= (django.views.static.serve)
        if public_view or view_func.__name__ == "serve":
            return None
        else:
            # not a public view, if not authenticaded ask for login
            if not request.user.is_authenticated:
                return login_required(view_func)(request, *view_args, **view_kwargs)

            prenotazioni_view = getattr(view_func, "prenotazioni", False)
            try:
                prenotazioni_user = request.user.prenotazioni
            except ObjectDoesNotExist:
                prenotazioni_user = False

            if prenotazioni_user and not prenotazioni_view:
                # messages.error(request, "Gli utenti del servizio prenotazioni non hanno accesso a questa pagina.")
                return HttpResponseRedirect(reverse("tamPrenotazioni"))

            elif not prenotazioni_user and prenotazioni_view:
                # messages.error(request, "I conducenti non possono accedere alle prenotazioni.")
                return HttpResponseRedirect(reverse("tamCorse"))
            else:
                if request.user.is_authenticated:
                    # everything is OK proceed with other middlewares
                    return None
                else:
                    # we are not logged in so let login_required redirect us
                    return login_required(view_func)(request, *view_args, **view_kwargs)


def csrf_failure_view(request, reason=""):
    response = render(request, "403.html", {})
    response.status_code = 403
    message_tokens = [
        "%s got hit in the face with Forbidden shovel" % request.user,
        "in: %s" % request.path,
    ]
    post_data = request.POST.copy()
    if "password" in post_data:
        del post_data["password"]
    if "HTTP_REFERER" in request.environ:
        message_tokens.append("from: %s" % request.environ["HTTP_REFERER"])
    message_tokens.append("POST: %s\n" % post_data)
    if False:  # ok, let's disable notifications of 403, if not settings.DEBUG
        mail_admins("403 alert", "\n".join(message_tokens))
    logger.warning("\n".join(message_tokens))
    return response
