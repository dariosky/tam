# coding=utf-8
import logging
import sys

import django
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render
from django.template import Template, RequestContext

from prenotazioni.views.tam_email import ADMIN_MAIL, notifyByMail

logger = logging.getLogger(__name__)


def errors500(request, template_name="500.html"):
    exc_type, exc, trackback = sys.exc_info()
    return render(request, template_name, locals())


def errors400(request, template_name="404.html"):
    return render(request, template_name, {})


def errorview(request):
    # mail_admins(subject='Message admins', message='Bla bla bla')
    if request.user.is_superuser:
        logger.error("There was an error on TaM. Normally should be reported via mail")
        raise Exception("Eccezione di test.")


def pingview(request):
    error = False
    results = ["{{host}}", "ok from django %s" % ".".join(map(str, django.VERSION[:3]))]

    response = Template("\n".join(results)).render(RequestContext(request))
    return HttpResponse(
        response, status=200 if not error else 500, content_type="text/plain"
    )


@user_passes_test(lambda user: user.is_superuser)
def email_test(request):
    results = [
        "Email sent to admins: %s" % ADMIN_MAIL,
        "backend: %s" % settings.EMAIL_BACKEND,
    ]
    notifyByMail(
        to=[ADMIN_MAIL],
        subject="Test email with %s" % settings.EMAIL_BACKEND,
        body="This is the body of the message",
    )
    response = Template("\n".join(results)).render(RequestContext(request))
    return HttpResponse(response, status=200, content_type="text/plain")
