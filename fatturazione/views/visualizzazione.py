#coding:utf-8

from django.template.context import RequestContext
from django.shortcuts import render_to_response
from fatturazione.models import Fattura, RigaFattura
import datetime
from tam.views.tamviews import parseDateString
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.aggregates import Max
from fatturazione.views.util import ultimoProgressivoFattura
from django.conf import settings
from django.core.urlresolvers import reverse
from fatturazione.views.pdf import render_to_reportlab#, render_with_pisa
from tam.models import logAction
from django.db import transaction
from decimal import Decimal

@permission_required('fatturazione.view', '/')
def view_fatture(request, template_name="5.lista-fatture.djhtml"):
	data_start = parseDateString(# dal primo del mese scorso
									request.GET.get("data_start"),
									default=(datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
								)
	data_end = parseDateString(# all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today()
								)

	lista_consorzio = Fattura.objects.filter(tipo='1', data__gte=data_start, data__lte=data_end)
#	lista_consorzio = lista_consorzio.annotate(valore=Sum(F('righe__prezzo')*(1+F('righe__iva')/100)))
	#TODO: (Django 1.4) dovrei annotare prezzo*1+iva/100, non si può fare attualmente
	lista_conducente = Fattura.objects.filter(tipo='2', data__gte=data_start, data__lte=data_end)
	lista_ricevute = Fattura.objects.filter(tipo='3', data__gte=data_start, data__lte=data_end)

	return render_to_response(template_name,
                              {
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundleJS": ('tamUI.js',),
								"mediabundleCSS": ('tamUI.css',),

								"lista_consorzio":lista_consorzio,
								"lista_conducente":lista_conducente,
								"lista_ricevute":lista_ricevute,

                              },
                              context_instance=RequestContext(request))


@permission_required('fatturazione.view', '/')
def fattura(request, id_fattura=None, anno=None, progressivo=None, tipo=None, template_name="6.fattura.djhtml"):
	""" Vedo la fattura ed (eventualmente) ne consento la modifica """
	try:
		if id_fattura:
			fattura = Fattura.objects.get(id=id_fattura)
		else:
			fattura = Fattura.objects.get(tipo=tipo, anno=anno, progressivo=progressivo)
	except Fattura.DoesNotExist:
		request.user.message_set.create(message="Fattura non trovata.")
		return HttpResponseRedirect(reverse('tamVisualizzazioneFatture'))

	bigEdit = request.user.has_perm('fatturazione.generate')
	smallEdit = request.user.has_perm('fatturazione.smalledit') and fattura.tipo == '2'
	editable = bigEdit or smallEdit
	readonly = not editable

	if request.is_ajax():
		action = request.POST.get('action')
		if action == 'delete-fat':
			if not request.user.has_perm('fatturazione.generate'):
				return HttpResponse('Non hai permessi per cancellare le fatture.', status=400)
			# cancello l'intera fattura.
			# se ho successo, restituisco l'url a cui andare
			message = "%s eliminata." % fattura.nome_fattura()
			try:
				logAction('C', instance=fattura, description=message, user=request.user)
				fattura.delete()
			except:
				return HttpResponse('Non sono riuscito a cancellare la fattura.', status=400)
			request.user.message_set.create(message=message)
			return HttpResponse(reverse('tamVisualizzazioneFatture'), status=200)

		if action == 'delete-row':
			if not request.user.has_perm('fatturazione.generate'):
				return HttpResponse('Non hai permessi per cancellare le righe delle fatture.', status=400)
			try:
				rowid = int(request.POST.get('row'))
				#if rowid in fattura.righe.values_list('id', flat=True):
				riga = fattura.righe.get(id=rowid)
				logAction('C', instance=fattura, description="Riga eliminata.", user=request.user)
				riga.delete()
				return HttpResponse('Riga eliminata.', status=200)
			except Exception, e:
				return HttpResponse('Impossibile trovare la riga.\n%s' % e, status=500)

		if action == 'append-row':
			if not request.user.has_perm('fatturazione.generate'):
				return HttpResponse('Non hai permessi sufficienti per aggiungere righe.', status=400)
			ultimaRiga = fattura.righe.aggregate(Max('riga'))['riga__max'] or 0
			riga = RigaFattura(descrizione="riga inserita manualmente",
							qta=1,
							prezzo=0,
							iva=10 if fattura.tipo in ('1', '2') else 0,
							riga=ultimaRiga + 10)
			logAction('C', instance=fattura, description="Riga inserita manualmente.", user=request.user)
			riga.save()
			fattura.righe.add(riga)
			return render_to_response('6.fattura-riga.inc.djhtml',
									{
										"riga":riga,
										'readonly': readonly,
										'bigEdit': bigEdit,
										'smallEdit': smallEdit,
		                            },
		                            context_instance=RequestContext(request))

		if action == 'set':
			object_id = request.POST.get('id')
			smallcampi_modificabili = ('fat_anno', 'fat_progressivo')
			if request.user.has_perm('fatturazione.smalledit') \
					and fattura.tipo == '2'  \
					and (object_id in smallcampi_modificabili or object_id.startswith('riga-desc-')):
				# posso modificare il campo in quanto è una modifica consentita
				pass
			else:
				if not request.user.has_perm('fatturazione.generate'):
					return HttpResponse('Non hai permessi sufficienti per modificare le fatture.', status=400)


			object_value = request.POST.get('value')
			header_ids = {'fat_mittente':'emessa_da', 'fat_note':'note', 'fat_destinatario':'emessa_a',
							'fat_anno':'anno', 'fat_progressivo':'progressivo',
						}
			header_numerici = ['fat_anno', 'fat_progressivo']
			logAction('C', instance=fattura, description="Valore modificato.", user=request.user)
			if object_id in header_ids:
#				print("cambio il valore di testata da %s a %s" % ( getattr(fattura, header_ids[object_id]),
#																	object_value)
#							)
				if object_id in header_numerici:
					if object_value.strip() == '':	# converto, nei valori numerici, le stringhe vuote in None
						object_value = None
					else:
						try:
							object_value = int(object_value.replace(',', '.'))	# altrimenti richiedo un numerico
						except Exception, e:
							return HttpResponse('Ho bisogno di un valore numerico.', status=500)
				if object_id == "fat_progressivo" and fattura.tipo == 1:
					esistenti = Fattura.objects.filter(anno=fattura.anno, progressivo=int(object_value), tipo=fattura.tipo)
					if esistenti.count() > 0:
						return HttpResponse("Esiste già una fattura con questo progressivo.", status=500)
				#print header_ids[object_id], "=",  object_value
				setattr(fattura, header_ids[object_id], object_value)
				fattura.save()
				return HttpResponse('Header changed.', status=200)
			else:
				row_ids = {'riga-desc-':'descrizione', 'riga-qta-':'qta', 'riga-prezzo-':'prezzo', 'riga-iva-':'iva'}
				row_numerici = ['riga-qta-', 'riga-prezzo-', 'riga-iva-']
				for prefix in row_ids.keys():
					if object_id.startswith(prefix):
						try:
							riga_id = int(object_id[len(prefix):])
							riga = fattura.righe.get(id=riga_id)
						except:
							return HttpResponse('Non ho trovato la riga corrispondente a %s.' % object_id, status=500)
						if prefix in row_numerici:
							#print "Converto il valore in un numerico"
							# tolgo i punti delle migliaia e metto il punto come separatore decimali
							object_value = object_value.replace(".", "").replace(",", ".")
							if object_value == '':
								object_value = 0
							else:
								try:
									object_value = object_value.replace(',', '.')
									if object_id.startswith('riga-prezzo-'):
										#print "Converto in Decimal:", object_value
										object_value = Decimal(object_value)
									else:	# converto in int
										#print "Converto in int:", object_value
										object_value = int(object_value)
								except Exception, e:
									print e
									return HttpResponse('Ho bisogno di un valore numerico.', status=500)
						#print "cambio la riga %d" % riga_id
						#print "imposto il valore %s" % object_value
						setattr(riga, row_ids[prefix], object_value)
						riga.save()
						return HttpResponse('OK.', status=200)
				return HttpResponse('Non conosco il campo %s.' % object_id, status=500)
			return HttpResponse('OK.', status=200)
		return HttpResponse('Azione sconosciuta.', status=500)


#	print "generate: ", request.user.has_perm('fatturazione.generate')
#	print "smalledit: ", request.user.has_perm('fatturazione.smalledit')
#	print "tipo: ", fattura.tipo
#	print "readonly: ", readonly
	return render_to_response(template_name,
                              {
								"fattura":fattura,
								'readonly': readonly,
								'bigEdit': bigEdit,
								'smallEdit': smallEdit,
                              },
                              context_instance=RequestContext(request))


@permission_required('fatturazione.generate', '/')
@transaction.commit_on_success
def nuova_fattura(request, tipo):
	if tipo == "1":
		anno = datetime.date.today().year
		ultimo = ultimoProgressivoFattura(anno, tipo=tipo)
		progressivo = ultimo + 1
	else:
		anno = None
		progressivo = None
	if tipo == '3':
		# le ricevute hanno sempre come data l'ultimo fine mese precedente
		data_fattura = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
	else:
		data_fattura = datetime.date.today()


	fattura = Fattura(
					anno=anno,
					tipo=tipo,
					progressivo=progressivo,
					data=data_fattura
					)
	if tipo == "1":
		fattura.emessa_da = settings.DATI_CONSORZIO
	elif tipo == "2":
		fattura.emessa_a = settings.DATI_CONSORZIO
	fattura.save()
	message = "Creata la %s %s." % (fattura.nome_fattura(), fattura.descrittore())
	request.user.message_set.create(message=message)
	logAction('C', instance=fattura, description=message, user=request.user)
	return HttpResponseRedirect(fattura.url())


# *********************************** EXPORT IN PDF ******************************

@permission_required('fatturazione.view', '/')
def exportfattura(request, id_fattura, export_type='html'):
#	response['Content-Disposition'] = 'attachment; filename="fattura %s.pdf"' % id_fattura
	try:
		fattura = Fattura.objects.get(id=id_fattura)
	except Fattura.DoesNotExist:
		request.user.message_set.create(message="Fattura non trovata.")
		return HttpResponseRedirect(reverse('tamVisualizzazioneFatture'))
	context = {"fattura":fattura, "readonly":True, 'export_type':export_type}
	template_name = 'fat_model/export_fattura_1.djhtml'
#	tamFatturaPdf(fattura, response)	# popola la response con il file
#	if export_type == "pisa":
#		return render_with_pisa(template_name, context)
	if export_type == 'pdf':
		return render_to_reportlab(context)
	else:	# html output by default
		return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

