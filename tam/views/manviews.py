# coding=utf-8
import django
from django.shortcuts import render_to_response
import sys
from django.http import HttpResponse
from django.template import Template, RequestContext


def errors500(request, template_name='500.html'):
	exc_type, exc, trackback = sys.exc_info()
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def errors400(request, template_name='404.html'):
	return render_to_response(template_name, {}, context_instance=RequestContext(request))


def errorview(request):
	# mail_admins(subject='Message admins', message='Bla bla bla')
	raise Exception("Eccezione di test.")


def pingview(request):
	error = False
	results = ['{{host}}', "ok from django %s" % ".".join(map(str, django.VERSION[:3]))]

	response = Template('\n'.join(results)).render(RequestContext(request))
	return HttpResponse(response, status=200 if not error else 500, content_type='text/plain')
