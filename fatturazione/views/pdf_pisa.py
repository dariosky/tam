import os

from django import http
from django.conf import settings


def render_with_pisa(template_src, context_dict):
    import xhtml2pdf.pisa as pisa
    from django.template.loader import get_template
    from django.template.context import Context
    from io import StringIO
    import cgi

    template = get_template(template_src)
    context = Context(context_dict)
    html = template.render(context)
    result = StringIO()
    pdf = pisa.pisaDocument(
        StringIO(html.encode("utf-8")), dest=result, link_callback=fetch_resources
    )
    if not pdf.err:
        return http.HttpResponse(result.getvalue(), content_type="application/pdf")
    return http.HttpResponse("We had some errors<pre>%s</pre>" % cgi.escape(html))


def fetch_resources(uri, rel):
    path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    return path
