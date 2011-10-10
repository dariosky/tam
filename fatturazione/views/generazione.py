#encoding: utf-8
'''
Created on 11/set/2011

@author: Dario
'''
import datetime
from tam.models import Viaggio, ProfiloUtente
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from fatturazione.models import Fattura, RigaFattura, nomi_fatture
from django.db.models import Q
from fatturazione.views.util import ultimoProgressivoFattura

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
from django.conf import settings

# Fatture consorzio: tutte le corse fatturabili, non fatturate con conducente confermato
filtro_consorzio = Q(fatturazione=True, conducente__isnull=False, riga_fattura=None)

# Fatture conducente: tutte le fatture consorzio senza una fattura_conducente_collegata
filtro_conducente = Q(fattura__tipo="1", fattura_conducente_collegata=None) # applicato sulle righe fatture

# se un viaggio ha sia pagamento differito che fatturazione, faccio solo la fattura
filtro_ricevute = Q(pagamento_differito=True, fatturazione=False, conducente__isnull=False, riga_fattura=None)



def lista_fatture(request, template_name="1.scelta_fatture.djhtml", tipo="1"):
	data_start = parseDateString(# dal primo del mese scorso
									request.GET.get("data_start"),
									default=(datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
								)
	data_end = parseDateString(# all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
								)
	# prendo i viaggi da fatturare
	viaggi = Viaggio.objects.filter(data__gte=data_start, data__lte=data_end)
	# FATTURE CONSORZIO ****************
	lista_consorzio = viaggi.filter(filtro_consorzio)
	lista_consorzio = lista_consorzio.order_by("cliente", "data").select_related().all()
	oggi = datetime.date.today()
	anno_consorzio = oggi.year
	progressivo_consorzio = ultimoProgressivoFattura(anno_consorzio, tipo) + 1
	
	# FATTURE CONDUCENTE ****************
	fatture = RigaFattura.objects.filter(viaggio__data__gte=data_start, viaggio__data__lte=data_end)
	lista_conducente = fatture.filter(filtro_conducente)
	
	# RICEVUTE CONDUCENTE
	lista_ricevute = viaggi.filter(filtro_ricevute)
	lista_ricevute = lista_ricevute.order_by("conducente", "cliente", "data").select_related().all()

	profile = ProfiloUtente.objects.get(user=request.user)
	luogoRiferimento = profile.luogo
	return render_to_response(template_name,
                              {
								"today": oggi,
								"luogoRiferimento":luogoRiferimento,
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundle": ('tamUI.css', 'tamUI.js'),
								
								"anno_consorzio":anno_consorzio,
								"progressivo_consorzio":progressivo_consorzio,
								"lista_consorzio":lista_consorzio,
								"lista_conducente":lista_conducente,
								"lista_ricevute":lista_ricevute,
                              },
                              context_instance=RequestContext(request))


def genera_fatture(request, tipo="1", filtro=filtro_consorzio, keys=["cliente"], template_name="2.fatturazione_consorzio.djhtml"):
	ids = request.GET.getlist("id")
	if not ids:
		request.user.message_set.create(message="Devi selezionare qualche corsa da fatturare.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	
	if tipo =="1":	# la generazione fatture consorzio richiede anno e progressivo
		try:
			anno = int(request.GET.get("anno"))
		except:
			request.user.message_set.create(message="Seleziona un anno numerico.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		try:
			progressivo = int(request.GET.get("progressivo", 1))
		except:
			request.user.message_set.create(message="Ho bisogno di un progressivo iniziale numerico.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		ultimo_progressivo = ultimoProgressivoFattura(anno, tipo)
		if ultimo_progressivo>=progressivo:
			request.user.message_set.create(message="Il progressivo è troppo piccolo, ho già la %s %s/%s." %(nomi_fatture[tipo], anno, ultimo_progressivo))
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

	
	lista = Viaggio.objects.filter(id__in=ids)
	lista = lista.filter(filtro)
	order_by = keys+["data"]	# ordino per chiave - quindi per data
	lista = lista.order_by(*order_by).select_related().all()
	if not lista:
		request.user.message_set.create(message="Tutte le corse selezionate sono già state fatturate.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	
	fatture = 0
	lastKey = None
	for viaggio in lista:
		key = [getattr(viaggio, keyName) for keyName in keys]
		if lastKey <> key:
			if lastKey <> None and tipo=='1': progressivo += 1
			lastKey = key
			fatture+=1
		viaggio.key = key
		if tipo=='1':
			viaggio.progressivo_fattura = progressivo

	if request.method == "POST":
		if request.POST.has_key("generate"):
			lastKey = None
			fatture_generate = 0
			
			for viaggio in lista:
				if viaggio.key <> lastKey:
					# TESTATA
					fattura = Fattura(tipo=tipo)
					fattura.data = datetime.date.today()
					if tipo == "1":	# fattura consorzio: da consorzio a cliente
						fattura.anno = anno
						fattura.progressivo = viaggio.progressivo_fattura
						fattura.emessa_da = settings.DATI_CONSORZIO
						fattura.emessa_a = viaggio.cliente.nome + "\n" + viaggio.cliente.dati
					elif tipo == "3": # ricevuta: da conducente a cliente
						fattura.emessa_da = viaggio.conducente.dati
						fattura.emessa_a = viaggio.cliente.nome + "\n" + viaggio.cliente.dati

					fattura.save()
					fatture_generate += 1
					riga = 1

					lastKey = viaggio.key

				# RIGHE dettaglio
				riga_fattura = RigaFattura()
				riga_fattura.riga = riga
				riga_fattura.descrizione = "%s" % viaggio
				riga_fattura.qta = 1
				riga_fattura.prezzo = viaggio.prezzo
				riga_fattura.iva = 10
				riga_fattura.viaggio = viaggio
				fattura.righe.add(riga_fattura)
				riga += 1

			print "Genero le %s" % nomi_fatture[tipo]
			request.user.message_set.create(message="Generate %d fatture." % fatture_generate)
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

	return render_to_response(template_name,
                              {
								"lista":lista,
								"mediabundle": ('tamUI.css', 'tamUI.js'),
								"tipo": nomi_fatture[tipo],
								"fatture":fatture,
#								"error_message":error_message,
                              },
                              context_instance=RequestContext(request))
	
def genera_conducente(request):
	return render_to_response("2.fatturazione_conducente.djhtml",
							{},
							context_instance=RequestContext(request))
