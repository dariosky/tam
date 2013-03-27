# coding=utf-8
import logging
import mimetypes
import os
from django.conf import settings
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.http.response import Http404


def serve_secure_file(request, path):
	absolute_path = os.path.join(settings.SECURE_STORE_LOCATION, path)
	if not os.path.isfile(absolute_path):
		raise Http404
	mime = mimetypes.guess_type(absolute_path)[0]
	logging.debug("Serving %s [%s]" % (path, mime))
	filename = os.path.basename(absolute_path)
	response = HttpResponse(FileWrapper(open(absolute_path, 'rb')), content_type=mime)
	#response = HttpResponse(file(absolute_path, 'rb'), content_type=mime)
	response['Content-Length'] = os.path.getsize(absolute_path)
	#response['Content-Disposition'] = "attachment; filename=%s" % filename
	return response
