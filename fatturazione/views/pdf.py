#coding: utf-8
from django.conf import settings
import os
from django.template.loader import get_template
from django.template.context import Context
import StringIO
import xhtml2pdf.pisa as pisa
from django import http
import cgi
import copy
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import * #@UnusedWildImport
from reportlab.pdfgen import canvas
from reportlab.platypus import Image as FlowableImage
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib import colors

def render_with_pisa(template_src, context_dict):
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






def render_to_reportlab(context):
	fattura = context.get('fattura')
	def firstPageTemplate(canvas, doc):
		canvas.setFont('Helvetica', 8)
		canvas.saveState()
		canvas.setAuthor(settings.LICENSE_OWNER)
		canvas.setCreator('TaM v.%s' % settings.TAM_VERSION)
		canvas._doc.info.producer = ('TaM invoices')
		canvas.setSubject(u"%s" % fattura.nome_fattura())
		canvas.setTitle(u"%s %s/%s" % (fattura.nome_fattura(), fattura.anno, fattura.progressivo))

		do_header(canvas)

#		canvas.restoreState()

	def do_header(canvas):
		canvas.drawImage(logoImage_path, x=1 * cm, y=height - 4 * cm, width=7 * cm, height=2.7 * cm)

		fattura_da = canvas.beginText()
		fattura_da.setTextOrigin(width - 8 * cm, height - 2 * cm)
		fattura_da.textLines(fattura.emessa_da)
		canvas.drawText(fattura_da)

		fattura_a = canvas.beginText()
		fattura_a.setTextOrigin(*fattura_da.getCursor())	# destinatario spaziato
		fattura_a.moveCursor(0, 1 * cm)
		fattura_a.textLines(fattura.emessa_a)
		#fattura_a
		canvas.drawText(fattura_a)


	response = http.HttpResponse(mimetype='application/pdf')
	width, height = portrait(A4)

	frames = [
				Frame(1.5 * cm, 3 * cm, width - 2.5 * cm, height - 10 * cm, showBoundary=1), #x,y, width, height
			]
	mainPage = PageTemplate(frames=frames, onPage=firstPageTemplate)
	laterPage = PageTemplate(frames=frames, onPage=firstPageTemplate)

	doc = BaseDocTemplate(response, leftMargin=2.5 * cm, pagesize=portrait(A4),
							pageTemplates=[mainPage, laterPage],
						)





	logoImage_path = os.path.join(settings.MEDIA_ROOT, 'fatture/logo.jpg')

	styles = getSampleStyleSheet()
	normalStyle = copy.deepcopy(styles['Normal'])
	normalStyle.fontSize = 8
	normalStyle.fontName = 'Helvetica'
	righeFattura = [
					('Descrizione', 'Q.tà', 'Prezzo', 'IVA %', 'Importo'),
				]
	
	for riga in fattura.righe.all():
		righeFattura.append((
							Paragraph(riga.descrizione, normalStyle),
							Paragraph("%s"%riga.qta, normalStyle),
							riga.prezzo, riga.iva, riga.val_totale()))
	righeStyle = TableStyle([
					('VALIGN', (0, 0), (-1, -1), 'TOP'),
					('ALIGN', (0, 0), (-1, -1), 'RIGHT'),	# globalmente allineato a destra...
					('ALIGN', (0, 0), (0, -1), 'LEFT'),	# tranne la prima colonna (con la descrizione)
					('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
					('FACE', (0, 0), (-1, -1), 'Helvetica'),
					('SIZE', (0, 0), (-1, -1), 8),
			])
	story = [ Table(righeFattura, style=righeStyle, repeatRows=1) ]


	doc.build(story)
	return response
