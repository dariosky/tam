#encoding: utf-8
'''
Created on 11/set/2011

@author: Dario
'''
import datetime
from tam.models import Viaggio, ProfiloUtente
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import logging

"""
Generazione fatture:
Chiedo di generare le fatture
	_fino a_
	anno
	progressivo
	
Generazione Fatture consorzio (a cliente):
	progressivo annuale, ma variabile
	iva 10% sulle corse
	possibilità di inserire una riga standard
	(logo)

Generazione Fatture Conducenti (a consorzio, tutte le corse fatturabili):
	progressivo in bianco
	(senza logo)
	
Generazione Ricevute (viaggi con pagamento posticipato)


"""


from django.shortcuts import render_to_response
from django.template.context import RequestContext
from tam.views import parseDateString


def generazione(request, template_name="generazione.djhtml"):
	data_start = parseDateString(	# dal primo del mese scorso
									request.GET.get("data_start"),
									default=(datetime.date.today().replace(day=1)-datetime.timedelta(days=1)).replace(day=1)
								)
	data_end = parseDateString( # all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today().replace(day=1)-datetime.timedelta(days=1)
								)
	# prendo i viaggi da fatturare
	da_consorzio = Viaggio.objects.filter(data__gte=data_start, data__lte=data_end, fatturazione=True, conducente__isnull=False).order_by("cliente").select_related()
	oggi = datetime.date.today()
	anno_consorzio = oggi.year
	progressivo_consorzio = 7
	profile = ProfiloUtente.objects.get(user=request.user)
	luogoRiferimento = profile.luogo
	return render_to_response(template_name,
                              {
								"today": oggi,
								"da_consorzio":da_consorzio,
								"luogoRiferimento":luogoRiferimento,
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundle": ('tamUI.css', 'tamUI.js'),
								"anno_consorzio":anno_consorzio,
								"progressivo_consorzio":progressivo_consorzio,
                              },
                              context_instance=RequestContext(request))


def genera_consorzio(request, template_name="generazione_consorzio.djhtml"):
	ids = request.GET.getlist("id")
	anno = request.GET.get("anno")
	if not ids:
		request.user.message_set.create(message="Devi selezionare qualche corsa da fatturare.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	da_consorzio = Viaggio.objects.filter(id__in = ids)
	da_consorzio = da_consorzio.filter(fatturazione=True, conducente__isnull=False)
	da_consorzio = da_consorzio.filter(riga_fattura=None)
	da_consorzio=da_consorzio.order_by("cliente", "data").select_related().all()
	if not da_consorzio:
		request.user.message_set.create(message="Tutte le corse selezionate sono già state fatturate.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	try:
		progressivo = int(request.GET.get("progressivo",1))
	except:
		request.user.message_set.create(message="Ho bisogno di un progressivo iniziale numerico.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))	
	lastCliente = None
	for viaggio in da_consorzio:
		if lastCliente<>viaggio.cliente:
			progressivo+=1
			lastCliente=viaggio.cliente
		viaggio.progressivo_fattura=progressivo
	
	if request.method=="post":
		if request.POST.has_key("generate"):
			logging.debug("Genero le fatture consorzio")
		
	return render_to_response(template_name,
                              {
								"anno":anno,
								"da_consorzio":da_consorzio,
								"mediabundle": ('tamUI.css', 'tamUI.js'),
                              },
                              context_instance=RequestContext(request))
