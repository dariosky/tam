# coding=utf-8
import logging

from brake.decorators import ratelimit
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView, logout_then_login as django_logout
from django.forms import forms
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _

from markViews import public
from modellog.actions import logAction
from tam.middleware.prevent_multisession import get_concurrent_sessions
from tam.ratelimit import get_client_ip

logger = logging.getLogger("tam.login")


class AuthenticationFormWrapped(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super(AuthenticationFormWrapped, self).__init__(request, *args, **kwargs)
        self.error_messages["multisession_forbidden"] = _(
            "Più dispositivi sono connessi con le stesse credenziali. "
            "Devi disconnetterti per collegarti qua."
        )

    def clean(self):
        cleaned_data = super(AuthenticationFormWrapped, self).clean()
        username = self.cleaned_data.get("username")
        request = self.request
        user = self.user_cache
        if settings.FORCE_SINGLE_DEVICE_SESSION and user:
            if hasattr(user, "prenotazioni"):
                utentePrenotazioni = user.prenotazioni
            else:
                utentePrenotazioni = None
            if not user.has_perm("tam.reset_sessions") and not utentePrenotazioni:
                concurrent_sessions = get_concurrent_sessions(request, user)
                if concurrent_sessions:
                    logger.warning("We have concurrent sessions: login forbidden")
                    logAction(
                        "L", description="Accesso proibito - multisessione", user=user
                    )
                    raise forms.ValidationError(
                        self.error_messages["multisession_forbidden"],
                        code="multisession_forbidden",
                        params={"username": username},
                    )
        return cleaned_data


@public
@ratelimit(method="POST")
def login(request):
    if getattr(request, "limited", False):
        messages = [
            "Too many requests on {path}. Page forbidden.".format(path=request.path),
            "From IP: %s" % get_client_ip(request),
        ]
        if request.method == "POST" and request.POST.get("username"):
            messages.append("Last try with username: %s" % request.POST.get("username"))
        logger.error("\n".join(messages))
        return render_to_response("429-limited.html", status=429)

    logged = request.user.is_authenticated and request.user.username

    class WrappedView(LoginView):
        template_name = "login.html"
        extra_context = {
            "logo_consorzio": settings.TRANSPARENT_LOGO,
            "nome_consorzio": settings.LICENSE_OWNER,
        }
        authentication_form = AuthenticationFormWrapped

    response = WrappedView.as_view()(request)
    if (
        request.user.is_authenticated and request.user.username != logged
    ):  # just logged in
        request.session["userAgent"] = request.META.get("HTTP_USER_AGENT")
        logger.debug("Login for %s" % request.user)
        logAction("L", description="Accesso effettuato", user=request.user)
    else:
        if request.method == "POST":
            logger.debug("Login attempt failed")
        if request.is_ajax():
            return HttpResponseServerError("Please login")

    return response


@public
def logout(request):
    logged = request.user.is_authenticated and request.user
    response = django_logout(request, login_url="/")
    if not request.user.is_authenticated and logged:  # just logged out
        logger.debug("Logout user %s" % logged)
        logAction("O", description="Disconnesso", user=logged)
    return response
