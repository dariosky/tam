# coding=utf-8
import logging
import mimetypes
import os
from wsgiref.util import FileWrapper

from django.conf import settings
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.template import Context
from django.template.loader import get_template
from django.urls import reverse


def serve_secure_file(request, path):
    absolute_path = os.path.join(settings.SECURE_STORE_LOCATION, path)
    if not os.path.isfile(absolute_path):
        return HttpResponseRedirect(reverse("secure-404"))
    mime = mimetypes.guess_type(absolute_path)[0]
    logging.debug("Serving %s [%s]" % (path, mime))
    response = HttpResponse(FileWrapper(open(absolute_path, "rb")), content_type=mime)
    response["Content-Length"] = os.path.getsize(absolute_path)
    return response


def notfound(request):
    template = get_template("bigMessage.html")
    return HttpResponse(template.render(Context(dict(message="File non trovato"))))
