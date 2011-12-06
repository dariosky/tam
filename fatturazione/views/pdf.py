#coding: utf-8
from django.conf import settings
import os
from django.template.loader import get_template
from django.template.context import Context
import StringIO
import xhtml2pdf.pisa as pisa
from django import http
import cgi

def render_to_pdf(template_src, context_dict):
	template = get_template(template_src)
	context = Context(context_dict)
	html = template.render(context)
	result = StringIO.StringIO()
	pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("utf-8")), dest=result,
						link_callback=fetch_resources)
	if not pdf.err:
		return http.HttpResponse(result.getvalue(), mimetype='application/pdf')
	return http.HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))

def fetch_resources(uri, rel):
	path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
	return path
