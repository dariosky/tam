#coding: utf-8
from django.conf import settings
import os
from django import http
import copy
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Frame, Paragraph, PageBreak, KeepTogether, TableStyle, Table, Preformatted #@UnusedImport
from reportlab.platypus.doctemplate import BaseDocTemplate, NextPageTemplate, PageTemplate #@UnusedImport
from reportlab.pdfgen import canvas #@UnusedImport
#from reportlab.platypus import Image as FlowableImage
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, portrait, landscape #@UnusedImport
from reportlab.lib import colors
from django.templatetags.l10n import localize
from fatturazione.views.money_util import moneyfmt, NumberedCanvas
import datetime
from fatturazione.views.generazione import FATTURE_PER_TIPO
from decimal import Decimal

logoImage_path = os.path.join(settings.MEDIA_ROOT, settings.OWNER_LOGO)
test = settings.DEBUG

styles = getSampleStyleSheet()
normalStyle = copy.deepcopy(styles['Normal'])
normalStyle.fontSize = 8
normalStyle.fontName = 'Helvetica'
data_ricevute_sdoppiate = datetime.date(2012, 4, 29)	# da questa data le ricevute create sono sdoppiate

def onPage(canvas, doc, da, a):
	width, height = canvas._doctemplate.pagesize
	canvas.saveState()
	fattura = doc.fattura
	fatturazione = doc.fatturazione
	stondata_style = ParagraphStyle("IntestazioneStondata", fontName='Helvetica', fontSize=8, leading=10,
								 borderRadius=5, borderWidth=1, borderColor=colors.silver, borderPadding=5)
	a_style = ParagraphStyle("Titolo della fattura", fontName='Helvetica', fontSize=8, leading=10)
	tipo = fattura.tipo

	# set PDF properties ***************
	canvas.setFont('Helvetica', 8)
	canvas.setAuthor(settings.LICENSE_OWNER)
	canvas.setCreator('TaM v.%s' % settings.TAM_VERSION)
	canvas._doc.info.producer = ('TaM invoices')
	canvas.setSubject(u"%s" % fattura.nome_fattura())
	if tipo == '3':
		nome = 'Ricevuta servizio TAXI'
	else:
		nome = 'Fattura'	# Fatture consorzio e conducente si chiamano semplicemente FATTURA
	descrittoreFattura = u"%s %s" % (nome, fattura.descrittore())
	canvas.setTitle(descrittoreFattura)

	# Header ***************
	y = height - doc.topMargin
	x = doc.leftMargin
	if test:
		canvas.setLineWidth(1)
		p = canvas.beginPath()
		p.moveTo(0, y); p.lineTo(width, y)
		canvas.drawPath(p)
	if fatturazione.mittente == "consorzio":
		logo_height = 2.5 * cm
		y -= logo_height
		canvas.drawImage(logoImage_path, x=x, y=y, width=7 * cm, height=logo_height)
	descrittore = Paragraph('<font size="14"><b>%s</b></font> del %s' % (descrittoreFattura, localize(fattura.data)),
							 a_style)
	descrittore.wrapOn(canvas, width / 2, y)
	descrittore.drawOn(canvas, x=x, y=y - descrittore.height)
	y -= descrittore.height + 10

	if fatturazione.mittente == "conducente":	# nelle fatture conducente metto il mittente a sinistra
		fattura_da = Paragraph(da.strip().replace('\n', '<br/>'), a_style)
		fattura_da.wrapOn(canvas, 6.5 * cm, 10 * cm)
		fattura_da.drawOn(canvas, x, y - fattura_da.height)
		y -= fattura_da.height
		y -= 0.2 * cm	# spacer tra mittente e destinatario

	if fattura.note:
		note = Preformatted(fattura.note, a_style)
		note.wrapOn(canvas, width / 2, 10 * cm)
		y = y - note.height - 8
		note.drawOn(canvas, 1 * cm, y=y)

	if tipo in ("3", '4'):
		y = y - 10
		ricevutaMultipla = (fattura.tipo == "3" and fattura.data >= data_ricevute_sdoppiate) or tipo == '4'
		testo_fisso = "Servizio trasporto emodializzato da Sua abitazione al centro emodialisi assistito e viceversa come da distinta."
		if ricevutaMultipla:
			testo_fisso = testo_fisso.replace("Servizio trasporto emodializzato", "Servizio di trasporto di tipo collettivo per emodializzato")

		testata_fissa = Paragraph("<font size='6'>%s</font>" % testo_fisso, a_style)
		testata_fissa.wrapOn(canvas, width / 2, 2 * cm)
		y = y - testata_fissa.height
		testata_fissa.drawOn(canvas, x, y)

	left_y = y - 8	# spacer finale

	if test:
		p = canvas.beginPath()
		p.moveTo(0, y); p.lineTo(width / 2, y)
		canvas.drawPath(p)

	# faccio la seconda colonna (destra) dell'header	
	y = height - doc.topMargin
	x = width - 8 * cm

	if not fatturazione.mittente == "conducente":	# nelle fatture conducente ho messo già il conducente a sinistra
		fattura_da = Paragraph(da.strip().replace('\n', '<br/>'), a_style)
		fattura_da.wrapOn(canvas, 6.5 * cm, 10 * cm)
		fattura_da.drawOn(canvas, x, y - fattura_da.height)
		y -= fattura_da.height
		y -= 0.1 * cm	# spacer tra mittente e destinatario

	fattura_a = Paragraph(a.replace('\n', '<br/>'), stondata_style)
	fattura_a.wrapOn(canvas, 6.5 * cm, 10 * cm)
	fattura_a.drawOn(canvas, x, y - fattura_a.height - fattura_a.style.borderPadding)

	y -= fattura_a.height + fattura_a.style.borderPadding * 2  # spazio finale
	right_y = y
	lower_y = min(left_y, right_y)

	y = lower_y

	if test:
		p = canvas.beginPath()
		p.moveTo(width / 2, y); p.lineTo(width, y)
		canvas.drawPath(p)

	note_finali_lines = []
	for footer_row in fattura.footer:
		note_finali_lines.append(footer_row)

	note_finali = Paragraph("<br/>".join(note_finali_lines), normalStyle)
	note_finali.wrap(width - doc.rightMargin - doc.leftMargin, 5 * cm)
	note_finali.drawOn(canvas, doc.leftMargin, doc.bottomMargin)

	# linea sotto l'intestazione
	canvas.setLineWidth(1)
	p = canvas.beginPath()
	p.moveTo(doc.leftMargin, y)
	p.lineTo(width - doc.rightMargin, y)
	canvas.drawPath(p)

	doc.pageTemplate.frames = [
			Frame(doc.leftMargin, doc.bottomMargin + note_finali.height,
				   width - (doc.leftMargin + doc.rightMargin), y - doc.bottomMargin - note_finali.height,
				   showBoundary=test), #x,y, width, height
		]

	canvas.setLineWidth(0.3)
	p = canvas.beginPath()
	p.moveTo(doc.leftMargin, doc.bottomMargin)
	p.lineTo(width - doc.rightMargin, doc.bottomMargin)
	canvas.drawPath(p)

	canvas.restoreState()


def onPageNormal(canvas, doc):
	#print "Normal"
	onPage(canvas, doc, da=doc.fattura.emessa_da, a=doc.fattura.emessa_a)

def onPageConducenteConsorzio(canvas, doc):
	templateID = "ConducenteConsorzio"
	currentTemplate = getattr(doc, 'lastTemplateID', doc.pageTemplates[0].id)
	if currentTemplate <> templateID:
		#print "Cambio da %s a %s" % (getattr(doc, 'lastTemplateID', None), templateID)
		doc.lastTemplateID = templateID

	#print "Conducente consorzio"
	descrittore_fattura = doc.fattura.descrittore
	doc.fattura.descrittore = lambda:""	# non specifico conducente
	onPage(canvas, doc, da=doc.fattura.emessa_da, a=settings.DATI_CONSORZIO)
	doc.fattura.descrittore = descrittore_fattura

def onPageConsorzioConducente(canvas, doc):
	templateID = "ConsorzioConducente"
	currentTemplate = getattr(doc, 'lastTemplateID', doc.pageTemplates[0].id)
	if currentTemplate <> templateID:
		#print "Cambio da %s a %s" % (getattr(doc, 'lastTemplateID', None), templateID)
		canvas.apply_page_numbers()
		doc.lastTemplateID = templateID

	descrittore_fattura = doc.fattura.descrittore
	doc.fattura.descrittore = lambda:""	# non specifico consorzio
	onPage(canvas, doc, da=settings.DATI_CONSORZIO, a=doc.fattura.emessa_a)
	doc.fattura.descrittore = descrittore_fattura


def render_to_reportlab(context):
	fattura = context.get('fattura')
	fattura.footer = context['invoices_footer']

	response = http.HttpResponse(mimetype='application/pdf')
	ricevutaMultipla = (fattura.tipo == "3") and fattura.data >= data_ricevute_sdoppiate

	if ricevutaMultipla:
		pageTemplates = [PageTemplate(id='ConducenteConsorzio', onPage=onPageConducenteConsorzio),
						 PageTemplate(id='ConsorzioConducente', onPage=onPageConsorzioConducente)
						]
	else:
		pageTemplates = [PageTemplate(id='Normale', onPage=onPageNormal)]

	width, height = portrait(A4)

	doc = BaseDocTemplate(response,
							pagesize=(width, height),
							leftMargin=1 * cm,
							rightMargin=1 * cm,
							bottomMargin=1.5 * cm,
							topMargin=1 * cm,
							showBoundary=test,
							pageTemplates=pageTemplates,
						)
	fatturazione = FATTURE_PER_TIPO[fattura.tipo]
	doc.fattura = fattura
	doc.fatturazione = fatturazione

	righeFattura = [
					('Descrizione', 'Q.tà', 'Prezzo', 'IVA %', 'Importo'),
				]

	righe = fattura.righe.all()

	if fatturazione.codice == "5" and not "Imposta di bollo" in [r.descrizione for r in righe]:
		#print "5 esente iva con barbatrucco"
		totale = sum([r.val_totale() for r in righe])
		netto = totale / Decimal(1.1)
		class RigaTotaleIvata(object):	# una riga che fa corrispondere il totale
			descrizione = "Servizi per consorzio."
			note = None
			qta = 1
			prezzo = netto
			iva = 10
			def val_imponibile(self):
				return self.prezzo
			def val_iva(self):
				return totale - netto
			def val_totale(self):
				return totale

		riga = RigaTotaleIvata()
		# la fattura ha totale pari al totale di tutte le righe
		# l'iva è fissa al 10% e il netto è calcolato di conseguenza
		imponibile = netto
		iva = totale - netto
		righe = [riga]

	else:
		imponibile = fattura.val_imponibile()
		iva = fattura.val_iva()


	for riga in righe:
		descrizione = riga.descrizione
		if riga.note: descrizione += " (%s)" % riga.note
		righeFattura.append((
							Paragraph(descrizione, normalStyle),
							Paragraph("%s" % riga.qta, normalStyle),
							moneyfmt(riga.prezzo), riga.iva, moneyfmt(riga.val_totale())
							))
	righeTotali = []
	righeTotali.append((
						'Imponibile', moneyfmt(imponibile)
						))
	righeTotali.append((
						'IVA', moneyfmt(iva)
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

	colWidths = ((width - doc.leftMargin - doc.rightMargin) - (1.6 * 4) * cm,) + (1.6 * cm,) * 4
	story = [ Table(righeFattura, style=righeStyle, repeatRows=1, colWidths=colWidths) ]
	story.append(KeepTogether(Table(righeTotali, style=totaliStyle,
									colWidths=(width - doc.leftMargin - doc.rightMargin - 1.6 * cm, 1.6 * cm))))

	if ricevutaMultipla:	# le ricevute si raddoppiano con 2 template diversi
		story = story + [NextPageTemplate("ConsorzioConducente"), PageBreak()] + story
	doc.build(story, canvasmaker=NumberedCanvas)
	return response

if __name__ == '__main__':
	from fatturazione.models import Fattura
	fattura = Fattura.objects.get(id=211)
	render_to_reportlab(context={"fattura":fattura, 'invoices_footer':settings.INVOICES_FOOTERS})
