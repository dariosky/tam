#coding:utf-8

from django.template.context import RequestContext
from django.shortcuts import render_to_response
from fatturazione.models import Fattura, RigaFattura, nomi_fatture
import datetime
from tam.views.tamviews import parseDateString
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models.aggregates import Max
from fatturazione.views.util import ultimoProgressivoFattura
from django.conf import settings
from django.core.urlresolvers import reverse
from fatturazione.views.pdf import render_to_pdf

@permission_required('fatturazione.view', '/')
def view_fatture(request, template_name="5.lista-fatture.djhtml"):
	data_start = parseDateString(# dal primo del mese scorso
									request.GET.get("data_start"),
									default=datetime.date.today().replace(day=1)
								)
	data_end = parseDateString(# all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today()
								)

	lista_consorzio = Fattura.objects.filter(tipo='1', data__gte=data_start, data__lte=data_end)
#	lista_consorzio = lista_consorzio.annotate(valore=Sum(F('righe__prezzo')*(1+F('righe__iva')/100)))
	#TODO: (Django 1.4) dovrei annotare prezzo*1+iva/100, non si può fare attualmente 
	return render_to_response(template_name,
                              {
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundleJS": ('tamUI.js',),
								"mediabundleCSS": ('tamUI.css',),

								"lista_consorzio":lista_consorzio,
#								"lista_conducente":lista_conducente,
#								"lista_ricevute":lista_ricevute,

                              },
                              context_instance=RequestContext(request))


@permission_required('fatturazione.view', '/')
def fattura(request, id_fattura, template_name="6.fattura.djhtml"):
	""" Vedo la fattura ed (eventualmente) ne consento la modifica """
	try:
		fattura = Fattura.objects.get(id=id_fattura)
	except Fattura.DoesNotExist:
		request.user.message_set.create(message="Fattura non trovata.")
		return HttpResponseRedirect(reverse('tamVisualizzazioneFatture'))


	if request.is_ajax():
		if not request.user.has_perm('fatturazione.generate'):
			return HttpResponse('Non hai permessi sufficienti per modificare le fatture.', status=400)
		action = request.POST.get('action')
		if action == 'delete-row':
			try:
				rowid = int(request.POST.get('row'))
				#if rowid in fattura.righe.values_list('id', flat=True):
				riga = fattura.righe.get(id=rowid)
				riga.delete()
				return HttpResponse('Riga eliminata.', status=200)
			except Exception, e:
				return HttpResponse('Impossibile trovare la riga.\n%s' % e, status=500)
		if action == 'append-row':
			ultimaRiga = fattura.righe.aggregate(Max('riga'))['riga__max'] or 0
			riga = RigaFattura(descrizione="riga inserita manualmente",
							qta=1,
							prezzo=0,
							iva=10 if fattura.tipo in ('1', '2') else 0,
							riga=ultimaRiga + 10)
			riga.save()
			fattura.righe.add(riga)
			return render_to_response('6.fattura-riga.inc.djhtml',
									{
										"riga":riga,
		                            },
		                            context_instance=RequestContext(request))
		if action == 'set':
			object_id = request.POST.get('id')
			object_value = request.POST.get('value')
			header_ids = {'fat_mittente':'emessa_da', 'fat_note':'note', 'fat_destinatario':'emessa_a',
							'fat_anno':'anno', 'fat_progressivo':'progressivo',
						}
			if object_id in header_ids.keys():
#				print("cambio il valore di testata da %s a %s" % ( getattr(fattura, header_ids[object_id]),
#																	object_value)
#							)
				if object_id == "fat_progressivo":
					esistenti = Fattura.objects.filter(anno=fattura.anno, progressivo=int(object_value))
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
							print "converto il valore in un numerico"
							# tolgo i punti delle migliaia e metto il punto come separatore decimali
							object_value = object_value.replace(".", "").replace(",", ".")

						print "cambio la riga %d" % riga_id
						print "imposto il valore %s" % object_value
						setattr(riga, row_ids[prefix], object_value)
						riga.save()
						return HttpResponse('OK.', status=200)
				return HttpResponse('Non conosco il campo %s.' % object_id, status=500)
			return HttpResponse('OK.', status=200)
		return HttpResponse('Azione sconosciuta.', status=500)

	return render_to_response(template_name,
                              {
								"fattura":fattura,
                              },
                              context_instance=RequestContext(request))

@permission_required('fatturazione.generate', '/')
def nuova_fattura(request, tipo):
	anno = datetime.date.today().year
	ultimo = ultimoProgressivoFattura(anno, tipo=tipo)
	fattura = Fattura(
					anno=anno,
					tipo=tipo,
					progressivo=ultimo + 1,
					data=datetime.date.today()
					)
	if tipo == "1":
		fattura.emessa_da = settings.DATI_CONSORZIO
	fattura.save()
	request.user.message_set.create(message="Creata la fattura %s/%s." % (anno, fattura.progressivo))
	return HttpResponseRedirect(reverse("tamFattura", kwargs={'id_fattura': fattura.id}))


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
	template_name = 'fat_model/fattura_1.djhtml'
#	tamFatturaPdf(fattura, response)	# popola la response con il file
	if export_type == "pdf":
		return render_to_pdf(template_name, context)
	elif export_type == 'html':
		return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

