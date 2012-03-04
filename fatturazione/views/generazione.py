#encoding: utf-8
'''
Created on 11/set/2011

@author: Dario
'''
import datetime
from tam.models import Viaggio, ProfiloUtente, Conducente, logAction
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from fatturazione.models import Fattura, RigaFattura, nomi_fatture, nomi_plurale
from django.db.models import Q
from fatturazione.views.util import ultimoProgressivoFattura
from django.db import transaction
from django.db.models.aggregates import Max
from django.contrib.auth.decorators import permission_required
from decimal import Decimal
import random
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
from django.conf import settings

# Fatture consorzio: tutte le corse fatturabili, non fatturate con conducente confermato
filtro_consorzio = Q(fatturazione=True, conducente__isnull=False, riga_fattura=None) & \
					~ Q(conducente__nick__iexact='ANNUL') # tolgo le corse assegnate al conducente annullato

# Fatture conducente: tutte le fatture consorzio senza una fattura_conducente_collegata
# applicato sulle righe fatture
filtro_conducente = Q(fattura__tipo="1", fattura_conducente_collegata=None, conducente__attivo=True) & \
					~ Q(conducente__nick__iexact='ANNUL')

# se un viaggio ha sia pagamento differito che fatturazione, faccio solo la fattura
filtro_ricevute = Q(pagamento_differito=True, fatturazione=False, conducente__isnull=False, riga_fattura=None) & \
					~ Q(conducente__nick__iexact='ANNUL')


@permission_required('fatturazione.generate', '/')
def lista_fatture_generabili(request, template_name="1.scelta_fatture.djhtml", tipo="1"):
	data_start = parseDateString(# dal primo del mese scorso
									request.GET.get("data_start"),
									default=(datetime.date.today().replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
								)
	data_end = parseDateString(# all'ultimo del mese scorso
									request.GET.get("data_end"),
									default=datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
								)
	# prendo i viaggi da fatturare
	# dalla mezzanotte del primo giorno alla mezzanotte esclusa del giorno dopo l'ultimo
	viaggi = Viaggio.objects.filter(data__gte=data_start, data__lt=data_end + datetime.timedelta(days=1))
	# FATTURE CONSORZIO ****************
	lista_consorzio = viaggi.filter(filtro_consorzio)
	lista_consorzio = lista_consorzio.order_by("cliente", "data").all()\
						.select_related("da", "a", "cliente", "conducente", "passeggero", "viaggio")
	oggi = datetime.date.today()
	anno_consorzio = data_end.year
	progressivo_consorzio = ultimoProgressivoFattura(anno_consorzio, tipo) + 1

	# FATTURE CONDUCENTE ****************
	fatture = RigaFattura.objects.filter(viaggio__data__gte=data_start, viaggio__data__lte=data_end + datetime.timedelta(days=1))
	lista_conducente = fatture.filter(filtro_conducente).order_by("viaggio__conducente", "viaggio__cliente", "viaggio__data").all()\
		.select_related("viaggio__da", "viaggio__a", "viaggio__cliente", "viaggio__conducente", "viaggio__passeggero",
						 'fattura', 'conducente')

	# RICEVUTE CONDUCENTE
	lista_ricevute = viaggi.filter(filtro_ricevute)
	lista_ricevute = lista_ricevute.order_by("cliente", "passeggero", "data").all()\
		.select_related("da", "a", "cliente", "conducente", "passeggero", "viaggio")

	profile = ProfiloUtente.objects.get(user=request.user)
	luogoRiferimento = profile.luogo
	return render_to_response(template_name,
                              {
								"today": oggi,
								"luogoRiferimento":luogoRiferimento,
								"data_start":data_start,
								"data_end":data_end,
								"dontHilightFirst":True,
								"mediabundleJS": ('tamUI.js',),
								"mediabundleCSS": ('tamUI.css',),

								"anno_consorzio":anno_consorzio,
								"progressivo_consorzio":progressivo_consorzio,
								"lista_consorzio":lista_consorzio,
								"lista_conducente":lista_conducente,
								"lista_ricevute":lista_ricevute,
                              },
                              context_instance=RequestContext(request))

@transaction.commit_on_success
@permission_required('fatturazione.generate', '/')
def genera_fatture(request, template_name, tipo="1", filtro=filtro_consorzio, keys=["cliente"], order_by=None,
					manager=Viaggio.objects,
				):
	ids = request.POST.getlist("id")
	plurale = nomi_plurale[tipo]
	conducenti_ricevute = None
	anno = 0	# usato solo con le fatture consorzio

	if not ids:
		request.user.message_set.create(message="Devi selezionare qualche corsa da fatturare.")
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

	data_generazione = parseDateString(request.POST['data_generazione'])
	if tipo == "1":	# la generazione fatture consorzio richiede anno e progressivo - li controllo
		try:
			anno = int(request.POST.get("anno"))
		except:
			request.user.message_set.create(message="Seleziona un anno numerico.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		try:
			progressivo = int(request.POST.get("progressivo", 1))
		except:
			request.user.message_set.create(message="Ho bisogno di un progressivo iniziale numerico.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		ultimo_progressivo = ultimoProgressivoFattura(anno, tipo)
		if ultimo_progressivo >= progressivo:
			request.user.message_set.create(message="Il progressivo è troppo piccolo, ho già la %s %s/%s." % (nomi_fatture[tipo], anno, ultimo_progressivo))
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	else:
		progressivo = 0 # nelle ricevute lo uso per ciclare
	progressivo_iniziale = progressivo

	lista = manager.filter(id__in=ids)
	lista = lista.filter(filtro)
	if manager == Viaggio.objects:
		lista = lista.select_related("da", "a", "cliente", "conducente", "passeggero", "viaggio")
	elif manager == RigaFattura.objects:
		lista = lista.select_related("viaggio__da", "viaggio__a", "viaggio__cliente", "viaggio__conducente", "viaggio__passeggero",
						 'fattura', 'conducente')
	if order_by is None:
		order_by = keys + ["data"]	# ordino per chiave - quindi per data
	lista = lista.order_by(*order_by).all()
	if not lista:
		request.user.message_set.create(message="Tutte le %s selezionate sono già state fatturate." % plurale)
		return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
	fatture = 0

	if tipo == "3":	# ricevuto mi preparo una lista entro la quale ciclare di conducenti che emettono ricevuti
		conducenti_ricevute = Conducente.objects.filter(emette_ricevute=True)
		if conducenti_ricevute.count() == 0:
			request.user.message_set.create(message="Nessun conducente emette ricevute. Deve essercene almeno uno.")
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
		dati_conducenti_ricevute = {}
		for conducente in conducenti_ricevute:
			# mi annoto il n° di fatture emesse per ogni conducente, lo cambierò sotto contando il conducente scelto come se avesse già emesso
			conducente._ricevute = len(conducente.ricevute())
			dati_conducenti_ricevute[conducente.id] = conducente	# tengo i conducenti in un dizionario

	lastKey = None
	conducenteRicevuta = None
	for elemento in lista:
		key = [getattr(elemento, keyName) for keyName in keys]
		if lastKey <> key:
			if lastKey <> None: progressivo += 1
			if tipo == '3':
				""" scelgo ruotando tra tutti i conducenti che non hanno mai emesso prima o tra quelli che hanno emesso più tempo fa
					ruoto per progressivo
				"""
				emessa_a = (elemento.cliente.dati or elemento.cliente.nome) or (elemento.passeggero.dati or elemento.passeggero.nome)
				conducenti_precedenti = conducenti_ricevute.filter(fatture__fattura__emessa_a=emessa_a, fatture__fattura__tipo='3').annotate(Max("fatture__fattura__data"))\
								.order_by("fatture__fattura__data__max")

				conducenti_estraibili = [c for c in conducenti_ricevute]
				for c in conducenti_precedenti:
					logging.debug("elimino %d che ha fatturato il %s" % (c.id, c.fatture__fattura__data__max))
					del conducenti_estraibili[conducenti_estraibili.index(c)]	# tolgo quelli che hanno già fatturato
				if conducenti_estraibili:
#					print "Ho conducenti che non hanno mai fatturato li tolgo dagli estraibili."
					pass
				else:
#					print "Tutti hanno già fatturato. Ripesco negli estraibili quelli che non hanno fatturato al cliente da più tempo."
					data_vecchia = conducenti_precedenti[0].fatture__fattura__data__max
					for c in conducenti_precedenti:
						if c.fatture__fattura__data__max > data_vecchia: break
						# c è il mio conducente in ricevute, lo cerco nella lista dei conducenti_ricevute (mi serve la conta delle ricevute)
						conducente = dati_conducenti_ricevute[c.id]
						conducenti_estraibili.append(conducente)


#					conducenti_PerNumRicevute.append( (conducente._ricevute, conducente.id) )
#					conducenti_PerNumRicevute.sort() # ordino per n° di ricevute emesse
#					print "Numero ricevute / Conducenti", conducenti_PerNumRicevute
#					for numRicevute, cond_id in conducenti_PerNumRicevute: #@UnusedVariable
#						conducenti_estraibili.append(cond_id)

				#random.shuffle(conducenti_estraibili)	# randomizzo tra gli aventi diritto

				conducenti_estraibili.sort(lambda x, y: cmp(x._ricevute, y._ricevute)) # ordino per n° di ricevute		
				#print "Parimerito:", conducenti_estraibili
				#conducente = conducenti_estraibili[progressivo % len(conducenti_estraibili)]
				conducente = conducenti_estraibili[0] # pesco il primo
				#print "Pesco il primo: %s" % (conducente)
				conducente._ricevute += 1	# conto come se l'avesse già amessa
				conducenteRicevuta = conducente
			lastKey = key
			fatture += 1
		elemento.key = key
		if tipo == '1':
			elemento.progressivo_fattura = progressivo
			elemento.anno_fattura = anno
		if tipo == '3':
			elemento.conducente_ricevuta = conducenteRicevuta

	if request.method == "POST":
		if request.POST.has_key("generate"):
			lastKey = None
			fatture_generate = 0

			for elemento in lista:
				if tipo in ("1", "3"):
					viaggio = elemento
				else:
					viaggio = elemento.viaggio
				if elemento.key <> lastKey:
					# TESTATA
					fattura = Fattura(tipo=tipo)
					data_fattura = data_generazione
#					if tipo == '3':
#						# le ricevute hanno sempre come data l'ultimo fine mese precedente
#						data_fattura = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
#					else:
#						data_fattura = datetime.date.today()

					fattura.data = data_fattura
					if tipo in ('1', '3'):	# popolo il destinatario della fattura
						if viaggio.cliente:
							fattura.cliente = viaggio.cliente
							fattura.emessa_a = viaggio.cliente.dati or viaggio.cliente.nome
						else:
							fattura.passeggero = viaggio.passeggero
							fattura.emessa_a = viaggio.passeggero.dati or viaggio.passeggero.nome

					if tipo == "1":	# fattura consorzio: da consorzio a cliente
						fattura.anno = anno
						fattura.progressivo = viaggio.progressivo_fattura
						fattura.emessa_da = settings.DATI_CONSORZIO
						fattura.note = 'Pagamento: Bonifico bancario 30 giorni data fattura'
					elif tipo == "3": # ricevuta: da conducente a cliente
						fattura.emessa_da = viaggio.conducente_ricevuta.dati or viaggio.conducente_ricevuta.nome
					elif tipo == "2": #fattura conducente
						fattura.emessa_da = viaggio.conducente.dati or viaggio.conducente.nome
						fattura.emessa_a = settings.DATI_CONSORZIO
						if viaggio:
							# nelle fatture conducente derivanti da un viaggio...
							# il cliente non è il destinatario. E può essere diverso per ogni riga
							pass
							# lascio il cliente in testata a None
							# il nome del cliente lo metto nelle note della riga.
#							if viaggio.cliente:
#								fattura.cliente = viaggio.cliente
#							else:
#								fattura.passeggero = viaggio.passeggero

					fattura.save()
					fatture_generate += 1
					riga = 10
					if tipo == "3":
						# per le 
						riga_fattura = RigaFattura(descrizione="Imposta di bollo", qta=1, iva=0, prezzo=Decimal("1.81"), riga=riga)
						fattura.righe.add(riga_fattura)
						riga += 10

					lastKey = elemento.key

				# RIGHE dettaglio
				riga_fattura = RigaFattura()
				riga_fattura.riga = riga	# progressivo riga
				if tipo in ("1", "3"):
					riga_fattura.descrizione = "%s-%s %s %dpax %s" % \
								(viaggio.da, viaggio.a, viaggio.data.strftime("%d/%m/%Y"),
									viaggio.numero_passeggeri, "taxi" if viaggio.esclusivo else "collettivo")
					riga_fattura.qta = 1
					riga_fattura.prezzo = viaggio.prezzo

					if viaggio.prezzo_sosta > 0:	# se ho una sosta, aggiungo il prezzo della sosta in fattura
						riga_fattura.prezzo += viaggio.prezzo_sosta
						riga_fattura.descrizione += " + sosta"

					riga_fattura.iva = 10 if tipo == "1" else 0
					riga_fattura.viaggio = viaggio
				else:
					campi_da_riportare = "descrizione", "qta", "iva"
					for campo in campi_da_riportare:
						setattr(riga_fattura, campo, getattr(elemento, campo))
					if viaggio:
						# uso il prezzo del viaggio, non della fattura consorzio
						riga_fattura.prezzo = viaggio.prezzo if viaggio else elemento.prezzo
						if viaggio.cliente:
							riga_fattura.note = viaggio.cliente.nome
						elif viaggio.passeggero:
							riga_fattura.note = viaggio.passeggero.nome
					else:
						riga_fattura.prezzo = elemento.prezzo	# ... a meno che il viaggio non manchi
					riga_fattura.riga_fattura_consorzio = elemento
				if tipo == '3':
					riga_fattura.conducente = elemento.conducente_ricevuta	# nelle ricevute i conducenti abilitati si ciclano per fatturare
				else:
					riga_fattura.conducente = elemento.conducente
				fattura.righe.add(riga_fattura)
				riga += 10

			message = "Generate %d %s." % (fatture_generate, plurale)
			request.user.message_set.create(message=message)
			logAction('C', instance=request.user, description=message, user=request.user)
			return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

	return render_to_response(template_name,
                              {
								# riporto i valori che mi arrivano dalla selezione
								"anno":anno,
								"progressivo_iniziale":progressivo_iniziale,

								"lista":lista,
								"mediabundleJS": ('tamUI.js',),
								"mediabundleCSS": ('tamUI.css',),
								"tipo": nomi_fatture[tipo],
								"fatture":fatture,
								"plurale":plurale,
#								"error_message":error_message,
								'conducenti_ricevute':conducenti_ricevute,
								'data_generazione':data_generazione,
                              },
                              context_instance=RequestContext(request))
