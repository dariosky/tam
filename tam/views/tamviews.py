#coding: utf-8
from django.shortcuts import render_to_response, HttpResponse, get_object_or_404
from django.http import HttpResponseRedirect	#use the redirects
#from django.contrib import auth	# I'll use authentication
from django.contrib.auth.models import User, Group
from django import forms
from django.utils.translation import ugettext as _
from django.template.context import RequestContext	 # Context with steroid
import datetime
from tam.models import Luogo, get_classifiche, Cliente, \
	PrezzoListino, Bacino, Tratta, Conducente, Conguaglio, Listino, \
	ProfiloUtente, Viaggio, Passeggero
from modellog.actions import logAction
import time
from django.db import IntegrityError
#from django.db import connection
from django.core.paginator import Paginator
from genericUtils import *
from django.db import models

# Creo gli eventuali permessi mancanti
from django.contrib.auth.management import create_permissions
from django.db.models import get_apps
from django.db.models.aggregates import Count
from django.views.decorators.cache import cache_page #@UnusedImport
from django.utils import simplejson
from django.core.urlresolvers import reverse
import logging
from decimal import Decimal
for app in get_apps():
	create_permissions(app, None, 2)
from django.db import connections
from django.contrib import messages
from django.conf import settings

class SmartPager(object):
	def addToResults(self, start, count):
		if start - self.lastPage > 1:
			self.results.append("...")
		for p in range(start, start + count):
			if p > 0 and p <= self.totalPages and (self.lastPage < p):
				self.results.append(p)
				self.lastPage = p

	def __init__(self, currentPage, totalPages):
		self.lastPage = 0
		self.results = []
		self.currentPage, self.totalPages = currentPage, totalPages
		self.addToResults(1, 2)
		self.addToResults(currentPage - 2, 5)
		self.addToResults(totalPages - 3, 4)

def parseDateString(s, default=None):
	try:
		t = time.strptime(s, '%d/%m/%Y')
		return datetime.date(t.tm_year, t.tm_mon, t.tm_mday)
	except:
		#logging.debug("Errore nel parsing della data.")
		return default

def listaCorse(request, template_name="corse/lista.html"):
	""" Schermata principale con la lista di tutte le corse """
	user = request.user
	profilo, created = ProfiloUtente.objects.get_or_create(user=user)
	dontHilightFirst = True
#	messages.debug(request, "Messaggio di debug.")
#	messages.info(request, "Messaggio di info.")
#	messages.success(request, "Messaggio di success.")
#	messages.warning(request, "Messaggio di warning.")
#	messages.error(request, "Messaggio di error.")

	outputFormat = request.GET.get('format', None)

#	precalcolati=0
#	for viaggio in Viaggio.objects.all(): #filter(html_tragitto=""):
#			if viaggio.padre is None: viaggio.updatePrecomp(force_save=True)
#			precalcolati+=1
#	if precalcolati: logging.debug("Ho precalcolato %d viaggi." % precalcolati)

#	if "togliAbbuoni" in request.GET:
#		viaggi_con_abbuoni= Viaggio.objects.filter(abbuono__gt=0)
#		for viaggio in viaggi_con_abbuoni:
#			if viaggio.tipo_abbuono=="F":
#				viaggio.abbuono_fisso+=viaggio.abbuono
#			else:
#				viaggio.abbuono_percentuale+=viaggio.abbuono
#			viaggio.abbuono=0
#			viaggio.save()
#		logging.debug("Rimossi gli abbuoni variabili da %d viaggi"%viaggi_con_abbuoni.count())

	if request.method == "POST":
		if not user.has_perm('tam.change_viaggio'):
			messages.error(request, "Non hai il permesso di modificare le corse.")
			return HttpResponseRedirect(reverse("tamCorse"))

		if 'assoType' in request.POST and request.POST['assoType']:
			gestisciAssociazioni(request, request.POST['assoType'], request.POST.getlist('viaggioId'))
			return HttpResponseRedirect("/")
		if "confirmed" in request.POST and "viaggio" in request.POST and "conducente" in request.POST:
			try:
				viaggio = Viaggio.objects.get(pk=request.POST["viaggio"])
			except Viaggio.DoesNotExist:
				messages.error(request, "Il viaggio che cerchi di confermare non esiste più.")
				return HttpResponseRedirect(reverse("tamCorse"))
			if viaggio.confirmed():
				messages.error(request, "Il viaggio è già stato confermato.")
				return HttpResponseRedirect(reverse("tamCorse"))
			conducente = Conducente.objects.get(pk=request.POST["conducente"])
			viaggio.conducente = conducente
			viaggio.conducente_confermato = True
			viaggio.updatePrecomp(force_save=True)
			return HttpResponseRedirect(reverse("tamCorse"))

	if profilo:
		luogoRiferimento = profilo.luogo
		if not luogoRiferimento:
			messages.warning(request, "Non hai ancora definito un luogo preferito.")

#	logging.debug("Comincio a caricare la lista corse")
	conducenti = Conducente.objects.all()	# list of all conducenti (even inactive ones) to filter
	clienti = Cliente.objects.filter(attivo=True).only('id', "nome")
	today = datetime.date.today()	# today to compare with viaggio.date
	adesso = datetime.datetime.now()
	distinct = False

	# ------------------ raccolgo tutti i possibili filtri
	filtriTipo = [
			u"Partenze", u"Arrivi", u"Fuori classifica", u"Venezia", u"Padova", u"Doppi Venezia", u"Doppi Padova",
	]
	filtriFlag = [u'Fatturate', u'Posticipate', u'Conto fine mese', u'Carta di credito', u'Quote consorzio', u'No quota consorzio', 'Sup.diurni', 'Sup.notturni']

	if u"filterFlag" in request.GET:
		filterFlag = request.GET["filterFlag"]
		request.session["filterFlag"] = filterFlag
	else:
		filterFlag = request.session.get("filterFlag", u"Tutti i flag")

	if u"filterType" in request.GET:
		filterType = request.GET["filterType"]
		request.session["filterType"] = filterType
	else:
		filterType = request.session.get("filterType", u"Tutti i tipi")


	if u"filterConducente" in request.GET:
		filterConducente = request.GET["filterConducente"]
		if filterConducente not in ("Non confermate", ""):
			try:
				filterConducente = int(filterConducente)
			except:
				filterConducente = ""
		request.session["filterConducente"] = filterConducente
	else:
		filterConducente = request.session.get("filterConducente", None)

	if u"filterCliente" in request.GET:
		filterCliente = request.GET["filterCliente"]
		if filterCliente != "Privato":
			try: filterCliente = int(filterCliente)
			except: filterCliente = ""
		request.session["filterCliente"] = filterCliente
	else:
		filterCliente = request.session.get("filterCliente", None)

	viaggi = Viaggio.objects.all()	# mostro tutti i figli, non raggruppo per padre
	if filterCliente or (filterFlag != "Tutti i flag") or outputFormat:		# non raggruppo
		distinct = True

#	viaggi=Viaggio.objects.filter(pk=5266)	#TMP
	if filterConducente:
		if filterConducente == "Non confermate":
			viaggi = viaggi.filter(conducente__isnull=True)
		else:
			viaggi = viaggi.filter(conducente=filterConducente)    # filtro il conducente
			conducenteFiltrato = Conducente.objects.get(id=filterConducente)

	filtriWhen = [ ("next", "Prossime corse"), ("all", "Tutte le date"), ("thisM", "Questo mese"), ("lastM", "Scorso mese")]
	if u"filterWhen" in request.GET:
		filterWhen = request.GET["filterWhen"]
		request.session["filterWhen"] = filterWhen
	else:
		filterWhen = request.session.get("filterWhen", "next")		# filtro predefinito (se non l'ho in sessione ne in get)

	data_inizio = None
	data_fine = None

	filtroWhenAvanzato = False
	if filterWhen == "advanced":
		filtroWhenAvanzato = True
		if request.GET.has_key('dstart'):
			try:
				data_inizio = parseDateString(request.GET.get('dstart'))
				request.session["dstart"] = data_inizio
			except:
				pass
		elif "dstart" in request.session:
			data_inizio = request.session["dstart"]

		if request.GET.has_key('dend'):
			try:
				data_fine = parseDateString(request.GET.get('dend'))
				request.session["dend"] = data_fine
			except:
				pass
		elif "dend" in request.session:
			data_fine = request.session["dend"]

	if data_inizio and data_fine and (data_fine <= data_inizio):
		data_fine = data_inizio + datetime.timedelta(days=1)

	if filterWhen == "next":       # prendo il minore tra 2 ore fa e mezzanotte scorsa
		data_ScorsaMezzanotte = adesso.replace(hour=0, minute=0)
		data_DueOreFa = adesso - datetime.timedelta(hours=2)
		data_inizio = min(data_ScorsaMezzanotte, data_DueOreFa)
		data_fine = adesso + datetime.timedelta(days=15)
	elif filterWhen == "thisM":
		data_inizio = adesso.replace(hour=0, minute=0, day=1)
		data_fine = (data_inizio + datetime.timedelta(days=32)).replace(hour=0, minute=0, day=1)
	elif filterWhen == "lastM":
		data_fine = adesso.replace(hour=0, minute=0, day=1)  # vado a inizio mese
		data_inizio = (data_fine - datetime.timedelta(days=1)).replace(day=1)      # vado a inizio del mese precedente

	# -----------------------------	filtro	------------------------------------
	if filterFlag != "Tutti i  flag":
		if filterFlag == u"Fatturate":
			viaggi = viaggi.filter(fatturazione=True)
		elif filterFlag == u"Posticipate":
			viaggi = viaggi.filter(pagamento_differito=True)
		elif filterFlag == u"Quote consorzio":
			viaggi = viaggi.filter(commissione__gt=0)
		elif filterFlag == u'No quota consorzio':
			viaggi = viaggi.filter(commissione=0)
		elif filterFlag == u'Conto fine mese':
			viaggi = viaggi.filter(incassato_albergo=True)
		elif filterFlag == u'Sup.diurni':
			viaggi = viaggi.filter(punti_diurni__gt=0)
		elif filterFlag == u'Sup.notturni':
			viaggi = viaggi.filter(punti_notturni__gt=0)
		elif filterFlag == u'Carta di credito':
			viaggi = viaggi.filter(cartaDiCredito=True)

	if filterCliente:
		if filterCliente == "Privato":
			viaggi = viaggi.filter(cliente__isnull=True)	# solo i privati
		else:
			viaggi = viaggi.filter(cliente__id=filterCliente)	# cliente specifico
			clienteFiltrato = Cliente.objects.get(id=filterCliente)

	if data_inizio: viaggi = viaggi.filter(data__gt=data_inizio)
	if data_fine: viaggi = viaggi.filter(data__lt=data_fine) # prossimi 15 giorni

	if filterType == u"Partenze":
		viaggi = viaggi.filter(arrivo=False)
#		viaggi=[viaggio for viaggio in viaggi if not viaggio.is_arrivo()]
	elif filterType == u"Arrivi":
		viaggi = viaggi.filter(arrivo=True)
#		viaggi=[viaggio for viaggio in viaggi if viaggio.is_arrivo()]
	elif filterType == u"Fuori classifica":
		viaggi = viaggi.filter(prezzoVenezia=0, prezzoPadova=0, punti_abbinata=0, prezzoDoppioPadova=0)
	elif filterType == u"Venezia":
		viaggi = viaggi.filter(prezzoVenezia__gt=0)
	elif filterType == u"Padova":
		viaggi = viaggi.filter(prezzoPadova__gt=0)
	elif filterType == u"Doppi Padova":
		viaggi = viaggi.filter(prezzoDoppioPadova__gt=0) | viaggi.filter(padre__prezzoDoppioPadova__gt=0)
	elif filterType == u"Doppi Venezia":
		viaggi = viaggi.filter(punti_abbinata__gt=0) | viaggi.filter(padre__punti_abbinata__gt=0)
#		viaggi=viaggi.filter(is_abbinata__in=('P', 'S'))
#		viaggi=[viaggio for viaggio in viaggi if viaggio.is_abbinata]

	paginator = Paginator(viaggi, settings.TAM_VIAGGI_PAGINA, orphans=10)	# pagine da tot viaggi
	tuttiViaggi = viaggi
	page = request.GET.get("page", 1)
	try:page = int(page)
	except: page = 1
	s = SmartPager(page, paginator.num_pages)
	paginator.smart_page_range = s.results
	try:
		thisPage = paginator.page(page)
		viaggi = thisPage.object_list
	except:
		messages.warning(request, "Pagina %d è vuota." % page)
		thisPage = None
		viaggi = []

	viaggi = viaggi.select_related("da", "a", "cliente", "conducente", "passeggero", "viaggio")
	num_viaggi = len(viaggi)
#	logging.debug("Ho caricato %d viaggi." % num_viaggi)
	classifiche = None	# ottengo le classifiche globali
	conducentiPerCapienza = {}

	for viaggio in viaggi:
		if not viaggio.conducente_confermato:	# se il viaggio non è confermato ottengo le classifiche (solo una volta)
			if classifiche is None:
				classifiche = get_classifiche()
#				for classi in classifiche[:2]:
#					logging.debug("%(conducente_nick)s %(priceMedium)s %(priceLong)s %(pricyLong)s %(abbinate)s %(num_disturbi_diurni)s %(num_disturbi_notturni)s"%classi)
			viaggio.classifica = viaggio.get_classifica(classifiche=classifiche, conducentiPerCapienza=conducentiPerCapienza) # ottengo la classifica di conducenti per questo viaggio


#	if settings.DEBUG:
#		q = [ q["sql"] for q in connections['default'].queries ]
#	#	q.sort()
#		qfile = file("querylog.sql", "w")
#		for query in q:
#			qfile.write("%s\n" % query)
#		qfile.close()
#		logging.debug("**** Number of queryes: %d ****" % len(connections['default'].queries))

	if outputFormat == 'xls':
		from tamXml import xlsResponse
		logAction(action='X', description="Export in Excel.", user=request.user, log_date=None)
		return xlsResponse(request, tuttiViaggi)
	mediabundleJS = ('tamCorse.js',)
	mediabundleCSS = ('tamUI.css',)
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def corsaClear(request, next=None):
	""" Delete session saves and return to a newCorsa """
	if not next: next = reverse("tamNuovaCorsa")
	for field in ("step1", "step2"):
		if field in request.session.keys():
			del request.session[field]	# sto ridefinendo il primo passo, lo tolgo dalla session
	return HttpResponseRedirect(next)

def corsa(request, id=None, step=1, template_name="nuova_corsa.html", delete=False, redirectOk="/"):
	user = request.user
	profilo, created = ProfiloUtente.objects.get_or_create(user=user)

	mediabundleJS = ('tamCorse.js',)
	mediabundleCSS = ('tamUI.css',)
	if id and not user.has_perm('tam.change_viaggio'):
		messages.error(request, "Non hai il permesso di modificare le corse.")
		return HttpResponseRedirect("/")
	if not user.has_perm('tam.add_viaggio'):
		messages.error(request, "Non hai il permesso di creare nuove corse.")
		return HttpResponseRedirect("/")

	if not profilo.luogo:
		messages.warning(request, "Non hai ancora definito un luogo preferito.")
	new = id is None
	step1 = request.session.get("step1") or {}
	dontHilightFirst = id or request.POST or "data" in step1	# non evidenziare il primo input se in modifica o se ho un POST

	if not id:				# popola la instance del viaggio
		viaggio = None
		destination1 = reverse("tamNuovaCorsa")
		destination2 = reverse("tamNuovaCorsa2")
	else:
		try:
			viaggio = Viaggio.objects.get(id=id)
		except Viaggio.DoesNotExist:
			messages.error(request, "Il viaggio indicato non esiste.")
			return HttpResponseRedirect(redirectOk)

		destination1 = reverse("tamNuovaCorsaId", kwargs={"id":id})
		destination2 = reverse("tamNuovaCorsa2Id", kwargs={"id":id})
	if viaggio and viaggio.vecchioConfermato() and not user.has_perm('tam.change_oldviaggio'):
		messages.error(request, "Non puoi cambiare i vecchi viaggi confermati.")
		return HttpResponseRedirect("/")

	if delete:
		if not id:
			messages.error(request, "Indicare la corsa da cancellare.")
			return HttpResponseRedirect(redirectOk)
		else:
			if request.method == "POST":
				if u"OK" in request.POST:
					viaggio.delete()
					messages.success(request, "Cancellata la corsa %s." % viaggio)
					return HttpResponseRedirect(redirectOk)
				else:
					return HttpResponseRedirect(redirectOk)
		return render_to_response(template_name, locals(), context_instance=RequestContext(request))      # fine del delete

	if step == 2:    # Integrity controls when accessing STEP2
		if (not id) and (not step1):	# sono in step2 ma non ho definito nulla della step1
			return HttpResponseRedirect(destination1)
		if "back" in request.GET:		# back to step1
			return HttpResponseRedirect(destination1)
	else:
		if viaggio and viaggio.conducente_confermato:	# per i viaggi confermati non posso cambiare nulla della prima schermata
#			return HttpResponseRedirect(destination2)
			pass

	from varieForm import ViaggioForm, ViaggioForm2
	formClasses = (ViaggioForm, ViaggioForm2)	# choose the right FormClass
	FormClass = formClasses[step - 1]

	if not "proceed" in request.POST:	# form will be unbound in no proceed is required (useful for reset)
		request.POST = {}

	form = FormClass(request.POST or None, instance=viaggio)


	# *************** GET DEFAULTS ********************************
	if id: # modifying
		cliente = viaggio.cliente
		form.initial["privato"] = (viaggio.cliente is None)
		if viaggio.esclusivo:
			form.initial["esclusivo"] = "t"
		else:
			form.initial["esclusivo"] = "c"

		if step == 1:
			if viaggio.is_abbinata: # ai figli non si può cambiare lo step1...
				# 21/2/2012 ... anche ai padri non lascio cambiare la prima pagina. Non voglio che cambi la data.
				messages.info(request, "Non puoi cambiare la prima pagina di dettagli finché la corsa è abbinata.")
				return HttpResponseRedirect(destination2)
				#form.fields['data'].widget.attrs['readonly'] = True

	else:  # new form
		cliente = step1.get("cliente", None)
#		form.initial["data"]=datetime.datetime.now()	# 5/10/2009 tolgo il default per la data
		if step == 1:
			if not step1:
				form.initial["da"] = form.initial["a"] = profilo.luogo.pk	# se non bound la form comincia partendo e finendo nel luogo predefinito
			else:
				form.initial.update(step1)
				if step1["esclusivo"]:
					form.initial["esclusivo"] = "t"
				else:
					form.initial["esclusivo"] = "c"
				referenceFields = ("da", "a", "passeggero", "cliente") # gli initial dei riferimenti devono essere chiavi non oggetti
				for field in referenceFields:
					try:
						if form.initial[field]: form.initial[field] = form.initial[field].pk
					except:
						pass
		elif step == 2:
#			"Sono in creazione, provo a popolare step2 con i default del cliente %s" % cliente
			fields = step1.copy()
			del fields["privato"]
			viaggioStep1 = Viaggio(**fields)
			viaggioStep1.luogoDiRiferimento = profilo.luogo
			viaggioStep1.updatePrecomp()
			da, a = step1["da"], step1["a"]
			viaggio = viaggioStep1	# in questo modo i dati dello step1 sono sempre in "viaggio"
#			"Cerco il prezzo listino da %s a %s." % (da, a)

			default = {}
			if cliente:
				default["fatturazione"] = cliente.fatturazione
				default["incassato_albergo"] = cliente.incassato_albergo
				default["pagamento_differito"] = cliente.pagamento_differito
				if cliente.commissione > 0: default["tipo_commissione"] = cliente.tipo_commissione
				default["commissione"] = cliente.commissione
				prezzolistino = None
				if cliente.listino:
					prezzolistino = cliente.listino.get_prezzo(da, a,
										tipo_servizio=viaggioStep1.esclusivo and "T" or "C",
										pax=viaggioStep1.numero_passeggeri)

				prezzoDaListinoNotturno = viaggioStep1.trattaInNotturna()
				prezzoDaListinoDiurno = not prezzoDaListinoNotturno

				if prezzolistino:
					if prezzoDaListinoDiurno:	# "Scelgo il prezzo normale"
						default["prezzo"] = prezzolistino.prezzo_diurno
					else:		# "Scelgo il prezzo notturno"
						default["prezzo"] = prezzolistino.prezzo_notturno

					if prezzolistino.flag_fatturazione == 'S':
						default["fatturazione"] = True
					elif prezzolistino.flag_fatturazione == 'N':
						default["fatturazione"] = False
					fatturazione_forzata = prezzolistino.flag_fatturazione

					if prezzolistino.commissione is not None:
						default["commissione"] = prezzolistino.commissione
						default["tipo_commissione"] = prezzolistino.tipo_commissione

			default["costo_autostrada"] = viaggioStep1.costo_autostrada_default()

			if da != profilo.luogo and da.speciale != "-":	# creando un viaggio di arrivo da una stazione/aeroporto
				logging.debug("Sto facendo un arrivo da un luogo speciale, aggiungo un abbuono di 5/10€")
				if da.speciale == "A":
					default["abbuono_fisso"] = 10
					da_speciale = "A"
				elif da.speciale == "S":
					default["abbuono_fisso"] = 5
					da_speciale = "S"

			form.initial.update(default)

	# *************** REMOVE FIELDS ********************************
	if step == 2:
		form.fields["note"].widget.attrs["cols"] = 80
		form.fields["note"].widget.attrs["rows"] = 4
		removefields = []
		if not cliente:	# campi rimossi ai privati
			removefields = [	"commissione", "tipo_commissione", # solo con i clienti
							"numero_pratica", 	# per le agenzie
#							"incassato_albergo", # per gli alberghi	# tolto il 14/2
#							"fatturazione", "pagamento_differito"
						]
		else:
#			if cliente.tipo!="H":
#				removefields.append("incassato_albergo")
			if cliente.tipo != "A":	# le agenzie hanno il numero di pratica
				removefields.append("numero_pratica")
		if not id:
			removefields += ["conducente_confermato"] # don't confirm on creation
		if id and viaggio and viaggio.padre:
				# "Escludo i campi che non vanno nei figli"
				removefields += ["conducente", "conducente_richiesto", "conducente_confermato"]

		for field in removefields:
			if field in form.fields: del form.fields[field]
		if id and viaggio.punti_abbinata and user.has_perm('tam.change_doppi'):
			kmTot = viaggio.get_kmtot()
			if kmTot:
				maxDoppi = viaggio.get_kmtot() / 120
			else: maxDoppi = 9	# imposto a 9 il numero massimo di casette nel caso per esempio non conosca le tratte
			form.fields["numDoppi"] = forms.IntegerField(label="Numero di doppi forzato",
								   help_text="max %d" % maxDoppi) # aggiungo i doppi forza a Nulla
			form.initial["numDoppi"] = viaggio.punti_abbinata
#			form.fields.append("ciao")

	# ****************  VALIDAZIONE E CREAZIONE ********************
	if form.is_valid():
		if step == 1:		# Passo allo step2
			if form.cleaned_data["data"] < datetime.datetime.now().replace(hour=0, minute=0):
				if not user.has_perm('tam.change_oldviaggio'):
					messages.error(request, "Non hai l'autorizzazione per inserire una corsa vecchia.")
					return HttpResponseRedirect("/")
			if id:
				viaggio = form.save()	#commit=True
				viaggio.updatePrecomp()
			else:
				request.session["step1"] = form.cleaned_data
			return HttpResponseRedirect(destination2)

		if step == 2:
			if id:
				viaggio = form.save() #commit=False
				if user.has_perm('tam.change_doppi'):
					numDoppi = form.cleaned_data.get("numDoppi", None)
				else:
					numDoppi = None

				viaggio.updatePrecomp(force_save=True, numDoppi=numDoppi)
			else:
				fields = step1.copy()
				fields.update(form.cleaned_data)

#				if not isinstance( fields["da"], Luogo ):
#					da, created = Luogo.objects.get_or_create( nome=fields["da"] )
#					fields["da"]=da
#
#				if not isinstance( fields["a"], Luogo ):
#					a, created = Luogo.objects.get_or_create( nome=fields["a"] )
#					fields["a"]=a

#				if ( not fields["privato"] ):
#					if  not isinstance( fields["cliente"], Cliente ):	# cliente
#						cliente, created = Cliente.objects.get_or_create( nome=fields["cliente"] )
#						fields["cliente"]=cliente
#				else:	# privato
#					if fields["passeggero"]:
#						passeggero, created = Passeggero.objects.get_or_create( nome=fields["passeggero"] )
#						fields["passeggero"]=passeggero

				del fields["privato"]
				nuovaCorsa = Viaggio(**fields)
				nuovaCorsa.luogoDiRiferimento = profilo.luogo
				nuovaCorsa.save()
				nuovaCorsa.updatePrecomp()
				viaggio = nuovaCorsa
				del request.session["step1"]
			if viaggio.passeggero and "datiPrivato" in request.POST:
				nuoviDati = request.POST["datiPrivato"]
				if nuoviDati.strip() == "": nuoviDati = None
				logging.debug("Cambio i dati del privato in %s" % nuoviDati)
				if nuoviDati != viaggio.passeggero.dati:
					viaggio.passeggero.dati = nuoviDati
					viaggio.passeggero.save();
					messages.success(request, "Modificati i dati del privato.")

			return HttpResponseRedirect(reverse("tamCorse"))
	#raise Exception("Sgnaps")
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def getList(request, model=Luogo.objects, field="nome", format="txt", fields=None):
	""" API Generica che restituisce un file di testo, con una lista di righe con tutte le istanze
		che abbiano il campo field uguale al campo q che ottengo via get
	"""
	q = request.GET.get("q")
	if q is not None:
		fieldApiString = {"%s__icontains" % field:q}
	else:
		fieldApiString = {}

	querySet = model.filter(**fieldApiString)

	if format == "txt":
		results = "\n".join([record.__unicode__() for record in querySet])
		return HttpResponse(results, mimetype="text/plain")
	if format == "json" and fields:
		records = querySet.values(*fields)
		results = [ [record[key] for key in fields] for record in records]
		return HttpResponse(simplejson.dumps(results), mimetype="application/javascript")


def clienti(request, template_name="clienti_e_listini.html"):
	listini = Listino.objects.annotate(Count('prezzolistino'))
	clienti = Cliente.objects.filter(attivo=True).select_related('listino')
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def cliente(request, template_name="cliente.html", nomeCliente=None, id_cliente=None):
	nuovo = (nomeCliente is None) and (id_cliente is None)
	if id_cliente: id_cliente = int(id_cliente)
	user = request.user
	actionName = getActionName(delete=False, nuovo=nuovo)
	if not user.has_perm('tam.%s_cliente' % actionName):
		messages.error(request, "Non hai il permesso di modificare i clienti.")
		return HttpResponseRedirect(reverse("tamListini"))

	class ClientForm(forms.ModelForm):
		class Meta:
			model = Cliente

	cliente = None
	if id_cliente:
		try:
			cliente = Cliente.objects.get(id=id_cliente)		# modifying an existing Client
			logging.debug("Modifica di %s" % cliente)
		except:
			messages.error(request, "Cliente inesistente.")
			return HttpResponseRedirect(reverse("tamListini"))
	if nomeCliente:
		try:
			cliente = Cliente.objects.get(nome=nomeCliente)		# modifying an existing Client
#			ClientForm=forms.form_for_instance(cliente)
		except Cliente.DoesNotExist:
#			ClientForm = forms.form_for_model(Cliente)
			ClientForm.base_fields["nome"].initial = nomeCliente	# creating a new client with name

	form = ClientForm(request.POST or None, instance=cliente)

	if form.is_valid():
		cliente = form.save()
		messages.success(request, "%s il cliente %s." % (nuovo and "Creato" or "Aggiornato", cliente))
		if "next" in request.GET:
			redirectOk = request.GET["next"]
		else:
			redirectOk = reverse("tamListini")
		return HttpResponseRedirect(redirectOk)
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def listino(request, template_name="listino.html", id=None, prezzoid=None):
	nuovo = id is None
	listino = None
	user = request.user

	if id:
		listino = Listino.objects.get(id=id)		# modifying an existing Client
#	else:
#		ListinoForm = forms.form_for_model(Listino)
	class ListinoForm(forms.ModelForm):
		class Meta:
			model = Listino
	form = ListinoForm(u"new_name" in request.POST and request.POST or None, instance=listino)

	if request.POST.get("da") and request.POST.get("da"):
		try: da = Luogo.objects.get(pk=request.POST.get("da"))
		except: da = None
		try: a = Luogo.objects.get(pk=request.POST.get("a"))
		except: a = None

	if "deletePrezzo" in request.POST:
		if da and a:
			prezzoL = PrezzoListino.objects.filter(tratta__da=da, tratta__a=a, listino=listino)
		else:
			prezzoL = None
		if prezzoL:
			if not user.has_perm('tam.delete_prezzolistino'):
				messages.error(request, "Non hai il permesso di cancellare i prezzi dal listino.")
				return HttpResponseRedirect(reverse("tamListini"))
			prezzoL[0].delete()
			messages.success(request, "Cancellato il prezzo %s." % prezzoL[0])
			return HttpResponseRedirect(reverse("tamListinoId", kwargs={"id": listino.id}))
		else:
			messages.error(request, "Non esiste una tratta da %s a %s." % (da, a))
	if form.is_valid():
		if u"new_name" in request.POST:
			try:
				actionName = getActionName(delete=False, nuovo=nuovo)
				if not user.has_perm('tam.%s_listino' % actionName):
					messages.error(request, "Non hai il permesso di %s i listini." % (nuovo and "creare" or "modificare"))
					return HttpResponseRedirect(reverse("tamListini"))
				listino = form.save()
				messages.success(request, "%s il listino %s." % (nuovo and "Creato" or "Aggiornato", listino))
				return HttpResponseRedirect(reverse("tamListinoId", kwargs={"id": listino.id}))
			except IntegrityError:
				form.errors["nome"] = (u"Esiste già un listino con lo stesso nome.",)

	class FormPrezzoListino(forms.ModelForm):
		da = forms.ModelChoiceField(Luogo.objects)
		a = forms.ModelChoiceField(Luogo.objects)
		class Meta:
			model = PrezzoListino
			exclude = ["tratta", "listino"]

	if prezzoid:
		try:
			prezzoListino = listino.prezzolistino_set.get(pk=prezzoid)
		except PrezzoListino.DoesNotExist:
			messages.error(request, "Il prezzo a cui provi ad accedere non esiste più.")
			return HttpResponseRedirect(reverse("tamListini"))

	else:
		prezzoListino = None

	priceForm = FormPrezzoListino(u"new_price" in request.POST and request.POST or None, instance=prezzoListino)
	if prezzoListino:
		priceForm.initial.update({   "da": prezzoListino.tratta.da.pk,
				    	      "a": prezzoListino.tratta.a.pk })
		nuovoPrezzo = False
	else:
		nuovoPrezzo = True

	if priceForm.is_valid():
		if u"new_price" in request.POST:
			actionName = getActionName(delete=False, nuovo=nuovoPrezzo)
			if not user.has_perm('tam.%s_prezzolistino' % actionName):
				messages.error(request, "Non hai il permesso di %s i prezzi di listino." % (nuovoPrezzo and "creare" or "modificare"))
				return HttpResponseRedirect(reverse("tamListini"))

			da = priceForm.cleaned_data["da"]
			a = priceForm.cleaned_data["a"]
			tratta, created = Tratta.objects.get_or_create(da=da, a=a)
			prezzo, created = listino.prezzolistino_set.get_or_create(tratta=tratta, listino=listino,
									tipo_servizio=priceForm.cleaned_data["tipo_servizio"],
									max_pax=priceForm.cleaned_data["max_pax"])
			prezzo.prezzo_diurno = priceForm.cleaned_data["prezzo_diurno"]
			prezzo.prezzo_notturno = priceForm.cleaned_data["prezzo_notturno"]
			prezzo.commissione = priceForm.cleaned_data["commissione"]
			prezzo.tipo_commissione = priceForm.cleaned_data["tipo_commissione"]
			prezzo.flag_fatturazione = priceForm.cleaned_data["flag_fatturazione"]
			prezzo.save()
			messages.success(request, "Ho aggiunto il prezzo %s." % prezzo)
			return HttpResponseRedirect(reverse("tamListinoId", kwargs={"id": listino.id}))

	# tutto l'ambaradam a seguire è solo per ordinare i prezzi per tratta.da, tratta.a
	if listino:
		prezziset = listino.prezzolistino_set.select_related().all()
		dictDa = {}
		for prezzo in prezziset:
			listDa = dictDa.get("%s" % prezzo.tratta.da.nome, [])
			listDa.append((prezzo.tratta.a.nome, prezzo.max_pax, prezzo))
			dictDa[prezzo.tratta.da.nome] = listDa
		prezzi = []
		keys = dictDa.keys()[:]
		keys.sort()			# ordino per destinazione e per max_pax
		for da in keys:
			dictDa[da].sort()
			for a, maxpax, prezzo in dictDa[da]:
				prezzi.append(prezzo)
	else:
		prezzi = None


	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def luoghi(request, template_name="luoghi_e_tratte.html"):
	""" Mostro tutti i luoghi suddivisi per bacino """
	unbacined = Luogo.objects.filter(bacino__isnull=True)
	bacini = Bacino.objects.all()
	tratte = Tratta.objects.select_related()
	mediabundleJS = ('tamUI.js',)
	mediabundleCSS = ('tamUI.css',)
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def conducente(*args, **kwargs):
	request = args and args[0] or kwargs['request']
	delete = kwargs.get('delete', False)
	if not request.user.has_perm('tam.change_classifiche_iniziali'):	# gli utenti base non possono cambiare molto dei conducenti
		kwargs["excludedFields"] = [	'classifica_iniziale_diurni', "classifica_iniziale_notturni",
									"classifica_iniziale_puntiDoppiVenezia", "classifica_iniziale_prezzoDoppiVenezia",
									"classifica_iniziale_doppiPadova", "classifica_iniziale_long", "classifica_iniziale_medium",
									"attivo"
								]
		if delete:
			messages.error(request, 'Devi avere i superpoteri per cancellare un conducente.')
			return HttpResponseRedirect("/")
	return bacino(*args, **kwargs)


def bacino(request, Model, template_name="bacinoOluogo.html", id=None, redirectOk="/", delete=False, unique=(("nome",),),
			note="", excludedFields=None):
	if "next" in request.GET:
		redirectOk = request.GET["next"]
	nuovo = id is None
	verbose_name = Model._meta.verbose_name
	verbose_name_plural = Model._meta.verbose_name_plural
	user = request.user
	actionName = getActionName(delete=delete, nuovo=nuovo)

	permissionName = "tam.%(action)s_%(module)s" % {"action":actionName, "module":Model._meta.module_name}
	allowed = user.has_perm(permissionName)
	if not allowed:
		messages.error(request, "Operazione non concessa.")
		return HttpResponseRedirect(redirectOk)

	class GenericModelForm(forms.ModelForm):
		def clean(self):
			for constraintList in unique:
				query = self.Meta.model.objects	# get all objects
				for field in constraintList:	# and filter all with the fields=contraints
					if not field in self.cleaned_data:
						return self.cleaned_data	# un campo di controllo è vuoto, fallirà dopo
					if isinstance(self.Meta.model._meta.get_field(field), models.CharField):
						# insensitive match only for CharField fields
						kwargs = { "%s__iexact" % field: self.cleaned_data[field] }
					else:
						kwargs = { "%s" % field: self.cleaned_data[field] }
					query = query.filter(**kwargs)
				if id: query = query.exclude(id=id)	# exclude current id if editing
				if query.count() > 0:
					raise forms.ValidationError(u"Esiste già un %s con questo %s." % (verbose_name, ", ".join(constraintList)))
			return self.cleaned_data
		class Meta:
			model = Model
			exclude = excludedFields

	instance = id and Model.objects.get(id=id) or None
	if not delete:	# creation or edit
		form = GenericModelForm(request.POST or None, instance=instance)
		if form.is_valid():
			instance = form.save()
			messages.success(request, "%s %s: %s." % (nuovo and "Creato" or "Aggiornato", verbose_name, instance))
			return HttpResponseRedirect(redirectOk)
	else:
		if not instance:
			messages.error(request, "Impossibile trovare l'oggetto da cancellare.")
			return HttpResponseRedirect(redirectOk)
		if request.method == "POST":
			if "OK" in request.POST:
				instance.delete()
				messages.success(request, "Cancellato il %s %s." % (verbose_name, instance))
				return HttpResponseRedirect(redirectOk)
			else:
				return HttpResponseRedirect(redirectOk)
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def privati(request, template_name="passeggeri.html"):
	""" Mostro tutti i passeggeri privati """
	privati = Passeggero.objects.all()
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def profilo(request, *args, **kwargs):
	instance, created = ProfiloUtente.objects.get_or_create(user=request.user)
	kwargs["id"] = instance.id
	kwargs["note"] = u"Puoi definire un po' di dettagli per l'utente %s." % request.user
	return bacino(request, *args, **kwargs)

# tengo la vista per vedere le classifiche separata
from tam.views.classifiche import classificheconducenti

def clonaListino(request, id, template_name="listino-clona.html"):
	user = request.user
	if not user.has_perm('tam.add_listino'):
		messages.error(request, "Non hai il permesso di creare un nuovo listino.")
		return HttpResponseRedirect(reverse("tamListini"))
	listino = get_object_or_404(Listino, pk=id)
	num_prezzi = listino.prezzolistino_set.count()
	class ListinoCloneForm(forms.Form):
		nome = forms.CharField()
		def clean_nome(self):
			nome = self.cleaned_data["nome"]
			try:
				Listino.objects.get(nome=nome)
				raise forms.ValidationError(u"Esiste già un listino chiamato '%s'." % nome)
			except Listino.DoesNotExist:
				return nome

	form = ListinoCloneForm(request.POST or None)
	if form.is_valid():
		new_listino = copy_model_instance(listino)

		new_listino.nome = form.cleaned_data["nome"]
		new_listino.save()
		for prezzo in listino.prezzolistino_set.all():
			new_prezzo = copy_model_instance(prezzo)
			new_prezzo.listino = new_listino
			new_prezzo.save()
		return HttpResponseRedirect(reverse("tamListini"))

	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def listinoDelete(request, id, template_name="listino-delete.html"):
	user = request.user
	if not user.has_perm('tam.delete_listino'):
		messages.error(request, "Non hai il permesso di cancellare i listini.")
		return HttpResponseRedirect(reverse("tamListini"))
	listino = get_object_or_404(Listino, pk=id)
	if request.method == "POST":
		listino.cliente_set.clear()	# se cancello un listino mantengo i clienti che lo usavano
#		for cliente in Cliente.objects.filter(listino=listino):
#			cliente.listino=None
#			cliente.save()

		listino.delete()
		return HttpResponseRedirect(reverse("tamListini"))

	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def resetAssociatiToDefault(viaggio, recurseOnChild=True):
	""" Dato un viaggio riporta padre e fratelli, o figli a alcuni settaggi standard come:
		Costo delle soste, costo autostrada
	"""
	if viaggio is None:
		return
	if viaggio.padre:
		resetAssociatiToDefault(viaggio.padre)	# applico sempre al padre
		return
	nodiDaSistemare = [viaggio]
	if recurseOnChild:
		nodiDaSistemare.extend(list(viaggio.viaggio_set.all()))
	for nodo in nodiDaSistemare:
		if nodo is None: continue
		logging.debug("Reset di %s" % viaggio.pk)
		nodo.costo_autostrada = nodo.costo_autostrada_default()      # ricalcolo l'autostrada

		nodo.conducente_confermato = False
		nodo.conducente = None
		nodo.save()


def gestisciAssociazioni(request, assoType, viaggiIds):
	""" Gestisce l'associazione disassociazione
		Riceve assoType con indicato cosa va fatto e una lista di viaggioId
		Azioni: link, unlink e bus
	"""
	logging.debug("Gestisco le associazioni [%s] %s" % (assoType, viaggiIds))
	user = request.user
	if not user.has_perm('tam.change_viaggio'):
		messages.error(request, "Non hai il permesso di modificare i viaggi.")
		return HttpResponseRedirect(reverse("tamCorse"))
	viaggi = Viaggio.objects.filter(pk__in=viaggiIds)
	toUpdate = []

	if len(viaggi) > 1:
		primo = viaggi[0]
	else:
		primo = None

	contatore = 1
	for viaggio in viaggi:
		logging.debug("%2s: %s di %s a %s" % (contatore, assoType, viaggio.pk, primo and primo.pk or "None"))

		if viaggio.padre and not viaggio.padre in toUpdate: # segno i padri precedenti da aggiornare
				toUpdate.append(viaggio.padre)

		if assoType == 'unlink':
			viaggio.padre = None
			if viaggio.da.speciale != "-":	# tolgo l'associazione a un viaggio da stazione/aeroporto
				logging.debug("Deassocio da un luogo speciale, rimetto l'eventuale abbuono di 5/10€")
				if viaggio.da.speciale == "A" and viaggio.abbuono_fisso != 10:
					messages.info(request, "Il %d° viaggio è da un aeroporto rimetto l'abbuono di 10€. Era di %d€." % (contatore, viaggio.abbuono_fisso))
					viaggio.abbuono_fisso = 10
				elif viaggio.da.speciale == "S" and viaggio.abbuono_fisso != 5:
					messages.info(request, "Il %d° viaggio è da una stazione rimetto l'abbuono di 5€. Era di %d€." % (contatore, viaggio.abbuono_fisso))
					viaggio.abbuono_fisso = 5
		elif assoType == 'link':
			if viaggio.da.speciale != "-":	# associando un viaggio da stazione/aeroporto
				logging.debug("Associo da un luogo speciale, tolgo l'eventuale abbuono di 5/10€")
				if viaggio.da.speciale == "A" and viaggio.abbuono_fisso == 10:
					messages.info(request, "Il %d° viaggio è da un aeroporto tolgo l'abbuono di 10€." % contatore)
					viaggio.abbuono_fisso = 0
				elif viaggio.da.speciale == "S" and viaggio.abbuono_fisso == 5:
					messages.info(request, "Il %d° viaggio è da una stazione tolgo l'abbuono di 5€." % contatore)
					viaggio.abbuono_fisso = 0

			if viaggio != primo:
				viaggio.padre = primo
			if contatore > 2:
				if viaggio.abbuono_fisso <> 5:
					messages.info(request, "Do un abbuono di 5€ al %d° viaggio perché oltre la 2nda tappa, era di %s€." % (contatore, viaggio.abbuono_fisso))
					viaggio.abbuono_fisso = 5


		if not viaggio in toUpdate:
			toUpdate.append(viaggio)
		viaggio.save()
		contatore += 1

	for viaggio in toUpdate:
		if viaggio.padre is None:	# sia il reset che l'update ricorre sui figli
			resetAssociatiToDefault(viaggio)
			viaggio.updatePrecomp()

def corsaCopy(request, id, template_name="corsa-copia.html"):
	user = request.user
	if not user.has_perm('tam.add_viaggio'):
		messages.error(request, "Non hai il permesso di creare i viaggi.")
		return HttpResponseRedirect(reverse("tamCorse"))
	corsa = get_object_or_404(Viaggio, pk=id)
	if corsa.padre: corsa = corsa.padre
	if corsa.is_abbinata:
		figli = corsa.viaggio_set.all()	# ottengo anche i figli

	class RecurrenceForm(forms.Form):
		repMode = forms.ChoiceField(label="Ricorrenza", choices=[("m", "Mensile"), ("w", "Settimanale"), ("d", "Giornaliero")])
		start = forms.DateField(label="Data iniziale", input_formats=[_('%d/%m/%Y')])
		end = forms.DateField(label="Data finale", input_formats=[_('%d/%m/%Y')])

	form = RecurrenceForm(request.POST or None)
	mediabundleJS = ('tamUI.js',)
	mediabundleCSS = ('tamUI.css',)
	dataIniziale = max(datetime.date.today(), corsa.data.date()) + datetime.timedelta(days=1)	# la data iniziale è quella della corsa + 1 e non prima di domani
	form.initial["start"] = dataIniziale.strftime('%d/%m/%Y')
	form.initial["end"] = dataIniziale.strftime('%d/%m/%Y')
	form.fields["start"].widget.attrs["id"] = "datastart"
	form.fields["end"].widget.attrs["id"] = "dataend"
	askForm = True
	if request.method == "POST" and not ("annulla" in request.POST):
		if form.is_valid():
			nuoviPadri = []
			day = form.cleaned_data["start"]
			end = form.cleaned_data["end"]
			type = form.cleaned_data["repMode"]
			occorrenze = 0
			while day <= end:
				nuoviPadri.append(day)

				if type == "d":
					day += datetime.timedelta(days=1)
				elif type == "w":
					day += datetime.timedelta(days=7)
				else:
					if day.month == 12:
						day = day.replace(year=day.year + 1)
						newMonth = 1
					else:
						newMonth = day.month + 1
					try:
						day = day.replace(month=newMonth)
					except ValueError:
						messages.warning(request, "Nel mese %d non c'è il giorno %d, mi fermo. Usa la copia per giorno se necessario." % (newMonth, day.day))
						break
				occorrenze += 1
				if occorrenze > 20:
					messages.error(request, "Non puoi creare più di 20 copie in una volta sola (per evitarti di fare danni accidentali).")
					break

			if "conferma" in request.POST:
				corseCreate = 0
				corseDaCopiare = [corsa]	# copio il padre...
				for figlio in corsa.viaggio_set.all(): # ... e tutti i figli
					corseDaCopiare.append(figlio)

				nuoviPadriCreati = []
				for nuovoPadre in nuoviPadri:
					deltaDays = nuovoPadre - corsa.data.date()
					logging.debug("Copio la corsa e la traslo di %s" % deltaDays)
					logging.debug("  ma le corse sono %d" % len(corseDaCopiare))
					for corsaOrigine in corseDaCopiare:
						nuovaCorsa = copy_model_instance(corsaOrigine)
						if corsaOrigine.padre is None:
							nuovoPadre = nuovaCorsa
						else:
							nuovaCorsa.padre = nuovoPadre

						nuovaCorsa.data += deltaDays
						corseCreate += 1

						nuovaCorsa.conducente_confermato = False	# le corse copiate mancano di alcune cose
						nuovaCorsa.pagato = False

						nuovaCorsa.save()
						logging.debug("Ho creato la corsa %s figlia di %s, %s" % (nuovaCorsa.pk, nuovaCorsa.padre and nuovaCorsa.padre.pk or "nissuni", nuovaCorsa.note))

						if nuovaCorsa.padre is None:
							nuoviPadriCreati.append(nuovaCorsa)

					for nuovoPadre in nuoviPadriCreati:
						nuovoPadre.updatePrecomp() # aggiorno tutto alla fine


				messages.success(request, "Ho creato %s copie della corsa (%d corse in tutto)." % (len(nuoviPadri), corseCreate))
				return HttpResponseRedirect(reverse("tamCorse"))

			for field in form.fields:
				form.fields[field].widget = forms.widgets.HiddenInput()	# la form è tutta hidden

			askForm = False

	jsui = askForm
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def util(request, template_name="utils/util.html"):
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def resetSessions(request, template_name="utils/resetSessions.html"):
	user = request.user
	if not user.is_superuser:
		messages.error(request, "Devi essere il superuser per cancellare le sessioni.")
		return HttpResponseRedirect("/")
	if request.method == "POST":
		if "reset" in request.POST:
			logging.debug("reset delle sessioni")
			from django.db import transaction
			connection = connections['default']
			cursor = connection.cursor()
			query = """
				delete from django_session
			"""
			cursor.execute(query)
			transaction.commit_unless_managed()

			#connection.commit()
			return HttpResponseRedirect("/")

	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def resetUserSession(selectedUser):
	from django.contrib.sessions.models import Session
	logging.debug("Cancello le sessioni dell'utente %s" % selectedUser.id)
	for ses in Session.objects.all():
		if ses.get_decoded().get('_auth_user_id') == selectedUser.id:
			ses.delete()

def permissions(request, username=None, template_name="utils/manageUsers.html"):
	user = request.user
	if not user.has_perm('auth.change_user'):
			messages.error(request, "Non hai l'autorizzazione a modificare i permessi.")
			return HttpResponseRedirect("/")
	users = User.objects.exclude(is_superuser=True).exclude(id=user.id)

	getUsername = request.GET.get("selectedUser", None)
	if getUsername:
		return HttpResponseRedirect(reverse("tamManage", kwargs={"username":getUsername}))
	if username:
		selectedUser = User.objects.get(username=username)
		if user == selectedUser:
			messages.error(request, "Non puoi modificare te stesso.")
			return HttpResponseRedirect(reverse("tamManage"))
		selectedGroups = selectedUser.groups.all()
		groups = Group.objects.all()
		for group in groups:
			if group in selectedGroups: group.selected = True

		password = request.POST.get("password", None)
		passwordbis = request.POST.get("passwordbis", None)
		if "change" in request.POST:	# effetto la modifica all'utente
			if password and password == passwordbis:
				# @type selectedUser auth.User
				selectedUser.set_password(password)
				selectedUser.save()
				messages.success(request, "Modificata la password all'utente %s." % selectedUser.username)
				resetUserSession(selectedUser)

			newGroups = request.POST.getlist("selectedGroup")
			selectedUser.groups.clear()
			logging.debug("clearing groups")
			for groupName in newGroups:
				group = Group.objects.get(name=groupName)
				selectedUser.groups.add(group)


			return HttpResponseRedirect(reverse("tamManage", kwargs={"username":selectedUser.username}))

	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def newUser(request, template_name="utils/newUser.html"):
	user = request.user
	profilo, created = ProfiloUtente.objects.get_or_create(user=user)
	if not user.has_perm('auth.add_user'):
			messages.error(request, "Non hai l'autorizzazione a creare nuovi utenti.")
			return HttpResponseRedirect(reverse("tamUtil"))

	from django.contrib.auth.forms import UserCreationForm
	form = UserCreationForm(request.POST or None)

	if form.is_valid():
		newUser = form.save()
		nuovoProfilo, created = ProfiloUtente.objects.get_or_create(user=newUser)
		# @type profilo tam.models.ProfiloUtente
		nuovoProfilo.luogo = profilo.luogo # prendo il luogo predefinito del creatore
		nuovoProfilo.save()
		messages.success(request, "Creato il nuovo utente in sola lettura %s." % newUser.username)
		return HttpResponseRedirect(reverse("tamManage", kwargs={"username":newUser.username}))

	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def delUser(request, username, template_name="utils/delUser.html"):
	user = request.user
	if not user.has_perm('auth.del_user'):
			messages.error(request, "Non hai l'autorizzazione per cancellare gli utenti.")
			return HttpResponseRedirect(reverse("tamUtil"))
	userToDelete = User.objects.get(username=username)
	if user == userToDelete:
		messages.error(request, "Non puoi cancellare te stesso.")
		return HttpResponseRedirect(reverse("tamManage"))
	if "sure" in request.POST:
		userToDelete.delete()
		messages.success(request, "Eliminato l'utente %s." % userToDelete.username)
		return HttpResponseRedirect(reverse("tamManage"))
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))


def passwordChangeAndReset(request, template_name="utils/changePassword.html"):
#	from django.contrib.auth.views import password_change
	from django.contrib.auth.forms import PasswordChangeForm
	form = PasswordChangeForm(request.user, request.POST or None)
	if form.is_valid():
		logging.debug("Cambio la password")
		form.save()
		resetUserSession(request.user)	# reset delle sessioni
		return HttpResponseRedirect('/')
#	response=password_change(request, template_name=template_name, post_change_redirect='/')
	return render_to_response(template_name, {'form': form }, context_instance=RequestContext(request))
