#coding: utf-8
from django.conf import settings
import os
from django import http
import copy
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import * #@UnusedWildImport
from reportlab.pdfgen import canvas
#from reportlab.platypus import Image as FlowableImage
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.lib import colors
from decimal import Decimal
from django.templatetags.l10n import localize

#def render_with_pisa(template_src, context_dict):
#	import xhtml2pdf.pisa as pisa
#	from django.template.loader import get_template
#	from django.template.context import Context
#	import StringIO
#	import cgi
#	template = get_template(template_src)
#	context = Context(context_dict)
#	html = template.render(context)
#	result = StringIO.StringIO()
#	pdf = pisa.pisaDocument(StringIO.StringIO(html.encode("utf-8")), dest=result,
#						link_callback=fetch_resources)
#	if not pdf.err:
#		return http.HttpResponse(result.getvalue(), mimetype='application/pdf')
#	return http.HttpResponse('We had some errors<pre>%s</pre>' % cgi.escape(html))

def fetch_resources(uri, rel):
	path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
	return path




def moneyfmt(value, places=2, curr='', sep='.', dp=',',
			 pos='', neg='-', trailneg=''):
	"""Convert Decimal to a money formatted string.
	
	places:  required number of places after the decimal point
	curr:	optional currency symbol before the sign (may be blank)
	sep:	 optional grouping separator (comma, period, space, or blank)
	dp:	  decimal point indicator (comma or period)
			 only specify as blank when places is zero
	pos:	 optional sign for positive numbers: '+', space or blank
	neg:	 optional sign for negative numbers: '-', '(', space or blank
	trailneg:optional trailing minus indicator:  '-', ')', space or blank
	
	>>> d = Decimal('-1234567.8901')
	>>> moneyfmt(d, curr='$')
	'-$1,234,567.89'
	>>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
	'1.234.568-'
	>>> moneyfmt(d, curr='$', neg='(', trailneg=')')
	'($1,234,567.89)'
	>>> moneyfmt(Decimal(123456789), sep=' ')
	'123 456 789.00'
	>>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
	'<0.02>'
	
	"""
	q = Decimal(10) ** -places	  # 2 places --> '0.01'
	sign, digits, exp = value.quantize(q).as_tuple()
	result = []
	digits = map(str, digits)
	build, next = result.append, digits.pop
	if sign:
		build(trailneg)
	for i in range(places):
		build(next() if digits else '0')
	build(dp)
	if not digits:
		build('0')
	i = 0
	while digits:
		build(next())
		i += 1
		if i == 3 and digits:
			i = 0
			build(sep)
	build(curr)
	build(neg if sign else pos)
	return ''.join(reversed(result))



def render_to_reportlab(context):
	fattura = context.get('fattura')
	test = settings.DEBUG

	class NumberedCanvas(canvas.Canvas):
		def __init__(self, *args, **kwargs):
			canvas.Canvas.__init__(self, *args, **kwargs)
			self._saved_page_states = []

		def showPage(self):
			self._saved_page_states.append(dict(self.__dict__))
			self._startPage()

		def save(self):
			"""add page info to each page (page x of y) if y>1"""
			num_pages = len(self._saved_page_states)

			for state in self._saved_page_states:
				self.__dict__.update(state)
				if num_pages > 1 or test:
					self.draw_page_number(num_pages)
				canvas.Canvas.showPage(self)

			canvas.Canvas.save(self)

		def draw_page_number(self, page_count):
			self.setFont("Helvetica", 7)
			self.drawRightString(width / 2, 1 * cm,
				"Pagina %d di %d" % (self._pageNumber, page_count))

	def firstPageTemplate(canvas, doc):
		canvas.saveState()
		stondata_style = ParagraphStyle("IntestazioneStondata", fontName='Helvetica', fontSize=8, leading=10,
									 borderRadius=10, borderWidth=1, borderColor=colors.silver, borderPadding=15)
		a_style = ParagraphStyle("Titolo della fattura", fontName='Helvetica', fontSize=8, leading=10)

		# set PDF properties ***************
		canvas.setFont('Helvetica', 8)
		canvas.setAuthor(settings.LICENSE_OWNER)
		canvas.setCreator('TaM v.%s' % settings.TAM_VERSION)
		canvas._doc.info.producer = ('TaM invoices')
		canvas.setSubject(u"%s" % fattura.nome_fattura())
		descrittoreFattura = u"%s %s" % (fattura.nome_fattura(), fattura.descrittore())
		canvas.setTitle(descrittoreFattura)

		# Header ***************
		topMargin = 1 * cm
		if fattura.tipo == "1":
			y = height - 2 * cm - topMargin
			canvas.drawImage(logoImage_path, x=1 * cm, y=y, width=7 * cm, height=2.5 * cm)
		else:
			y = height - topMargin
		descrittore = Paragraph('<font size="14"><b>%s</b></font> del %s' % (descrittoreFattura, localize(fattura.data)),
								 a_style)
		descrittore.wrapOn(canvas, width / 2, 2 * cm)
		y -= descrittore.height + 8
		descrittore.drawOn(canvas, x=1 * cm, y=y)


		if fattura.note:
			note = Preformatted(fattura.note, a_style)
			note.wrapOn(canvas, width / 2, 10 * cm)
			y = y - note.height - 8
			note.drawOn(canvas, 1 * cm, y=y)

		if fattura.tipo in ("3"):
			y = y - 10
			testata_fissa = Paragraph("<font size='6'>Servizio trasporto emodializzato da Sua Abitazione al centro emodialisi assistito e viceversa come da distinta.</font>", a_style)
			testata_fissa.wrapOn(canvas, width / 2, 2 * cm)
			y = y - testata_fissa.height
			testata_fissa.drawOn(canvas, 1 * cm, y=y)

		left_y = y - 8	# spacer finale

		if test:
			canvas.setLineWidth(4)
			p = canvas.beginPath()
			p.moveTo(0, y); p.lineTo(width / 2, y)
			canvas.drawPath(p)

		fattura_da = canvas.beginText()
		fattura_da.setTextOrigin(width - 8 * cm, height - topMargin - 0.5 * cm)
		fattura_da.textLines(fattura.emessa_da)
		canvas.drawText(fattura_da)

		fattura_a = Paragraph(fattura.emessa_a.replace('\n', '<br/>'), stondata_style)
		fattura_a.wrapOn(canvas, 6.5 * cm, 10 * cm)
		x, y = fattura_da.getCursor()

		spacerMittenteDestinatario = 0.5 * cm
		fattura_a.drawOn(canvas, x, y - fattura_a.height - spacerMittenteDestinatario)

		y -= fattura_a.height + fattura_a.style.borderPadding + spacerMittenteDestinatario
		right_y = y
		lower_y = min(left_y, right_y)

		y = lower_y

		if test:
			canvas.setLineWidth(4)
			p = canvas.beginPath()
			p.moveTo(width / 2, y); p.lineTo(width, y)
			canvas.drawPath(p)
		note_finali.drawOn(canvas, doc.leftMargin, doc.bottomMargin)

		doc.pageTemplate.frames = [
				Frame(doc.leftMargin, doc.bottomMargin + note_finali.height,
					   width - (doc.leftMargin + doc.rightMargin), y - doc.bottomMargin - note_finali.height,
					   showBoundary=test), #x,y, width, height
			]

		canvas.restoreState()


	response = http.HttpResponse(mimetype='application/pdf')
	width, height = portrait(A4)

	doc = BaseDocTemplate(response,
							pagesize=portrait(A4),
							leftMargin=1 * cm,
							rightMargin=1 * cm,
							bottomMargin=1.5 * cm,
							topMargin=1.5,
							showBoundary=test,
							pageTemplates=PageTemplate(onPage=firstPageTemplate),
						)



	logoImage_path = os.path.join(settings.MEDIA_ROOT, 'fatture/logo.jpg')

	styles = getSampleStyleSheet()
	normalStyle = copy.deepcopy(styles['Normal'])
	normalStyle.fontSize = 8
	normalStyle.fontName = 'Helvetica'

	note_finali_lines = []
	if fattura.tipo == "1":
		note_finali_lines.append("Si prega di effettuare il pagamento sul conto Corrente:")
		note_finali_lines.append("UNICREDIT BANCA SPA - Agenzia di Montegrotto Terme IBAN: IT94 x 02008 62680 000040451824")
	if fattura.tipo in ("3"):
		note_finali_lines.append("<font size='6'>Esente iva art. 10 comma 14 del DPR.633/72 integrato art. 10 comma 12 bis del 18/01/93 n°8.</font>")
	if fattura.tipo in ("1", "3"):
		note_finali_lines.append("<font size='6'>Ai sensi dell'art. 13 del D.L. 196/2003 sulla tutela della privacy, vi informiamo di aver inserito i dati anagrafici e fiscali che ci avete fornito nei nostri archivi informatici.</font>")

	note_finali = Paragraph("<br/>".join(note_finali_lines), normalStyle)
	note_finali.wrap(width - doc.rightMargin - doc.leftMargin, 5 * cm)

	righeFattura = [
					('Descrizione', 'Q.tà', 'Prezzo', 'IVA %', 'Importo'),
				]

	for riga in fattura.righe.all():
		descrizione = riga.descrizione
		if riga.note: descrizione += " (%s)" % riga.note
		righeFattura.append((
							Paragraph(descrizione, normalStyle),
							Paragraph("%s" % riga.qta, normalStyle),
							moneyfmt(riga.prezzo), riga.iva, moneyfmt(riga.val_totale())
							))
	righeTotali = []
	righeTotali.append((
						'Imponibile', moneyfmt(fattura.val_imponibile())
						))
	righeTotali.append((
						'IVA', moneyfmt(fattura.val_iva())
						))
	righeTotali.append((
						'TOTALE', moneyfmt(fattura.val_totale())
						))
	righeStyle = TableStyle([
					('VALIGN', (0, 0), (-1, -1), 'TOP'),
					('ALIGN', (0, 0), (-1, -1), 'RIGHT'), 	# globalmente allineato a destra...
					('ALIGN', (0, 0), (1, -1), 'LEFT'), 	# tranne la prima colonna (con la descrizione)
					('GRID', (0, 1), (-1, -1), 0.1, colors.grey),
					('FACE', (0, 0), (-1, -1), 'Helvetica'),

					('FACE', (0, 0), (-1, 0), 'Helvetica-Bold'), 	# header
					('SIZE', (0, 0), (-1, -1), 8),

					#('SPAN', (0, -1), (3, -1)),	# anziché mettere lo span qui aggiungo in coda una tabella diversa
			])
	totaliStyle = TableStyle([
							('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
							('GRID', (-1, 0), (-1, -1), 0.1, colors.grey),

							('FACE', (0, 0), (-1, -1), 'Helvetica'), 	# header
							('FACE', (0, -1), (-1, -1), 'Helvetica-Bold'), 	# Totale
							('SIZE', (0, 0), (-1, -1), 8),

						])

	colWidths = ((width - 2 * cm) - (1.6 * 4) * cm,) + (1.6 * cm,) * 4
	story = [ Table(righeFattura, style=righeStyle, repeatRows=1, colWidths=colWidths) ]
	story.append(KeepTogether(Table(righeTotali, style=totaliStyle, colWidths=(width - 2 * cm - 1.6 * cm, 1.6 * cm))))
	#story.append(Spacer(0, 0.5 * cm))
	#story.append(note_finali)

	doc.build(story, canvasmaker=NumberedCanvas)
	return response
