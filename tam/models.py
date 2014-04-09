# coding: utf-8
from django.db import models
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse  # to resolve named urls
from django.template.loader import render_to_string
from django.contrib.auth.models import User

try:
	from calendariopresenze.models import Calendar
except ImportError:
	Calendar = None

import tam.tamdates as tamdates
import datetime
from decimal import Decimal
import logging
from django.core.cache import cache
from django.db import connections
from django.conf import settings
import re
from tam.disturbi import fasce_semilineari, trovaDisturbi, fasce_uno_due
from django.db.models.deletion import SET_NULL, PROTECT
from django.contrib.staticfiles.storage import staticfiles_storage

TIPICLIENTE = (("H", "Hotel"), ("A", "Agenzia"), ("D", "Ditta"))  # se null nelle corse è un privato
TIPICOMMISSIONE = [("F", "€"), ("P", "%")]
TIPISERVIZIO = [("T", "Taxi"), ("C", "Collettivo")]

#cache_conducentiPerPersona = {} # Tengo un dizionari con tutti i conducenti con più di key persone
# per evitare di interrogare il DB ogni volta.
# quando cambio un conducente lo svuoto


#invalidation of cache-template-tag cache
#from django.utils.hashcompat import md5_constructor
#from django.utils.http import urlquote
#def invalidate_template_cache(fragment_name, *variables):
#	args = md5_constructor(u':'.join([urlquote(var) for var in variables]))
#	cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
#	cache.delete(cache_key)
# ******************

def reallySpaceless(s):
	""" Given a string, removes all double spaces and tab """
	s = re.sub('[\s\t][\s\t]+', " ", s, flags=re.DOTALL).strip()
	return s


class Luogo(models.Model):
	""" Indica un luogo, una destinazione conosciuta.
		Ogni luogo appartiene ad un bacino all'interno del quale verrano cercati gli accoppiamenti.
		Al luogo afferiranno i listini, le corse e tutto il resto.
	"""
	nome = models.CharField("Località ", max_length=25, unique=True)
	bacino = models.ForeignKey("Bacino", verbose_name="Bacino di appartenenza", null=True, blank=True)
	speciale = models.CharField("Luogo particolare", max_length=1,
	                            default="",
	                            choices=(("-", "-"), ("A", "Aeroporto"), ("S", "Stazione")))
	# una delle località sarà  la predefinita... tra le proprietà  dell'utente

	class Meta:
		verbose_name_plural = _("Luoghi")
		ordering = ["nome"]

	def __unicode__(self):
		if self.nome[0] == ".": return self.nome[1:]
		return self.nome

	def delete_url(self):
		return reverse("tamLuogoIdDel", kwargs={"id": self.id})

	def save(self, *args, **kwargs):
		if 'updateViaggi' in kwargs:
			updateViaggi = kwargs['updateViaggi']
			del (kwargs['updateViaggi'])
		else:
			updateViaggi = True
		super(Luogo, self).save(*args, **kwargs)
		if not updateViaggi: return
		# aggiorno tutte le corse precalcolate con quel luogo
		viaggiCoinvolti = Viaggio.objects.filter(tratta_start__da=self) | Viaggio.objects.filter(tratta_start__a=self) | \
		                  Viaggio.objects.filter(tratta__da=self) | Viaggio.objects.filter(tratta__a=self) | \
		                  Viaggio.objects.filter(tratta_end__da=self) | Viaggio.objects.filter(tratta_end__a=self)
		viaggiCoinvolti = viaggiCoinvolti.filter(conducente_confermato=False)  # ricalcolo tutti i non confermati
		for viaggio in viaggiCoinvolti:
			viaggio.updatePrecomp()


class Bacino(models.Model):
	""" I bacini sono dei gruppi di luoghi da cercare di accorpare nelle corse abbinate """
	nome = models.CharField(max_length=20, unique=True)

	class Meta:
		verbose_name_plural = _("Bacini")
		ordering = ["nome"]

	def __unicode__(self):
		return self.nome

	def delete_url(self):
		return reverse("tamBacinoIdDel", kwargs={"id": self.id})


class Tratta(models.Model):
	""" Indica un tragitto, con indicati i default di tempo, spazio e spese di autostrada """
	da = models.ForeignKey(Luogo, related_name="tempo_da")
	a = models.ForeignKey(Luogo, related_name="tempo_a")
	minuti = models.IntegerField(default=0)  # tempo di viaggio espresso in minuti
	km = models.IntegerField(default=0)
	costo_autostrada = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # fino a 9.999.999,99

	class Meta:
		verbose_name_plural = _("Tratte")
		unique_together = (("da", "a"),)
		#		order_with_respect_to="a"
		ordering = ["da", "a"]

	def __unicode__(self):
		return u"%s - %s: %dm., %dkm" % (self.da, self.a, self.minuti, self.km)

	def is_valid(self):
		""" Return true if the path have all it's information completed """
		return self.minuti and self.km

	def delete_url(self):
		return reverse("tamTrattaIdDel", kwargs={"id": self.id})

	def save(self, *args, **kwargs):
		""" Salvo la tratta """
		if 'updateViaggi' in kwargs:
			updateViaggi = kwargs['updateViaggi']
			del (kwargs['updateViaggi'])
		else:
			updateViaggi = True
		super(Tratta, self).save(*args, **kwargs)
		# invalida la cache
		keyword = ("tratta%s-%s" % (self.da.id, self.a.id)).replace(" ", "")
		cache.delete(keyword)

		if updateViaggi:
			# aggiorno tutte le corse precalcolate con questa tratta
			viaggiCoinvolti = Viaggio.objects.filter(tratta_start=self) | \
			                  Viaggio.objects.filter(tratta=self) | \
			                  Viaggio.objects.filter(tratta_end=self)
			viaggiCoinvolti = viaggiCoinvolti.filter(conducente_confermato=False)  # ricalcolo tutti i non confermati
			for viaggio in viaggiCoinvolti:
				viaggio.updatePrecomp()


def get_tratta(da, a):
	""" Ritorna una data DA-A, se non esiste, A-DA, se non esiste la crea """
	if not da or not a: return
	keyword = ("tratta%s-%s" % (da.id, a.id)).replace(" ", "")
	trattacache = cache.get(keyword)
	if trattacache:
		return trattacache
	#	logging.debug("Cerco la tratta %s - %s" % (da, a))
	result = None
	tratta = Tratta.objects.filter(da=da, a=a)
	if tratta.count():
		result = tratta[0]  # trovata la tratta esatta
	else:
		tratta = Tratta.objects.filter(da=a, a=da)
		if tratta.count():
			result = tratta[0]  # trovata la tratta inversa
		else:
			tratta = Tratta(da=da, a=a)
			tratta.save()
			result = tratta
	cache.set(keyword, result)  # keep in cache
	return result


class Viaggio(models.Model):
	""" Questa è una corsa, vecchia o nuova che sia. Tabella chiave di tutto. """
	# nell'inserimento chiedo inizialmente le basi
	data = models.DateTimeField("Data e ora", db_index=True)
	da = models.ForeignKey(Luogo, related_name="da")
	a = models.ForeignKey(Luogo, related_name="a")
	numero_passeggeri = models.IntegerField(default=1)
	esclusivo = models.BooleanField("Servizio taxi",
	                                default=True)  # se non è consentito il raggruppamento contemporaneo

	cliente = models.ForeignKey("Cliente", null=True, blank=True, db_index=True,
	                            on_delete=PROTECT)  # se null è un privato
	passeggero = models.ForeignKey("Passeggero", null=True, blank=True,
	                               on_delete=SET_NULL)  # eventuale passeggero se cliente 'Privato'

	prezzo = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # fino a 9999.99
	costo_autostrada = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # fino a 9999.99
	costo_sosta = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # fino a 9999.99

	#	abbuono=models.DecimalField(max_digits=9, decimal_places=2, default=0)	# fino a 9999.99
	#	tipo_abbuono=models.CharField("Tipo di abbuono", max_length=1, choices=tipiCommissione, default="F")
	abbuono_fisso = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # fino a 9999.99
	abbuono_percentuale = models.IntegerField(default=0)  # abbuono percentuale

	help_sosta = "Verrà aggiunto al prezzo scontato del %d%%" % settings.SCONTO_SOSTA if settings.SCONTO_SOSTA else ""
	prezzo_sosta = models.DecimalField(max_digits=9, decimal_places=2, default=0, help_text=help_sosta)

	incassato_albergo = models.BooleanField("Conto fine mese",
	                                        default=False)  # flag per indicare se la corsa è incassata dall'albergo (sarà utile per reportistica)
	fatturazione = models.BooleanField("Fatturazione richiesta", default=False)
	pagamento_differito = models.BooleanField("Fatturazione esente IVA", default=False)
	cartaDiCredito = models.BooleanField("Pagamento con carta di credito", default=False)
	commissione = models.DecimalField("Quota consorzio", max_digits=9, decimal_places=2, default=0)  #fissa in euro
	tipo_commissione = models.CharField("Tipo di quota", max_length=1, choices=TIPICOMMISSIONE, default="F")
	numero_pratica = models.CharField(max_length=20, null=True, blank=True)

	padre = models.ForeignKey("Viaggio", null=True, blank=True)  # l'eventuale viaggio padre nei raggruppamenti
	data_padre = models.DateTimeField("Data e ora padre", db_index=True, null=True, editable=False)
	id_padre = models.PositiveIntegerField("ID Gruppo", db_index=True, null=True, editable=False)

	conducente_richiesto = models.BooleanField("Escluso dai supplementari",
	                                           default=False)  # True quando il conducente è fissato
	conducente = models.ForeignKey("Conducente", null=True, blank=True,
	                               db_index=True)  # conducente (proposto o fissato)
	conducente_confermato = models.BooleanField("Conducente confermato",
	                                            default=False)  # True quando il conducente è fissato

	note = models.TextField(blank=True)
	pagato = models.BooleanField(default=False)

	luogoDiRiferimento = models.ForeignKey(Luogo, related_name="riferimento",
	                                       null=True)  # Luogo to calculate stats, in instance, should be populated on creation
	km_conguagliati = models.IntegerField("Km conguagliati", null=True, blank=True, default=0,
	                                      editable=False)  # per i padri della abbinate conta quanti km di abbinata sono già  stati conguagliati

	html_tragitto = models.TextField(blank=True, editable=False)
	tratta = models.ForeignKey(Tratta, null=True, blank=True, default=None, editable=False)
	tratta_start = models.ForeignKey(Tratta, null=True, blank=True, related_name='viaggio_start_set', editable=False)
	tratta_end = models.ForeignKey(Tratta, null=True, blank=True, related_name='viaggio_end_set', editable=False)
	is_abbinata = models.CharField(max_length=1, null=True, blank=True,
	                               editable=False)  # tipo di abbinata (null: non è abbinata, P: partenza, successiva altrimenti)
	punti_notturni = models.DecimalField(max_digits=6, decimal_places=2, default=0,
	                                     editable=False)  # float con 2 decimali
	punti_diurni = models.DecimalField(max_digits=6, decimal_places=2, default=0, editable=False)  # float
	km = models.IntegerField(default=0, editable=False)  # numero di chilometri per la riga (le 3 tratte)
	arrivo = models.BooleanField(default=True, editable=False)  # tipo di viaggio True se è un arrivo
	is_valid = models.BooleanField(default=True, editable=False)  # True se il viaggio ha tutte le tratte definite

	punti_abbinata = models.IntegerField(default=0, editable=False)
	prezzoPunti = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
	#	prezzoAbbinata=models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)	# prezzo sia del padre che di tutti i figli - non usato lo cancello 19/11

	prezzoVenezia = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
	prezzoPadova = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
	prezzoDoppioPadova = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
	prezzo_finale = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
	date_start = models.DateTimeField(editable=False,
	                                  default=tamdates.date_enforce(datetime.datetime(2009, 01, 01, 0, 0, 0)))
	annullato = models.BooleanField('Corsa annullata', default=False, editable=True)

	# per non dover fare query quando visualizzo il viaggio, mi imposto che deriva da una prenotazione
	is_prenotazione = models.BooleanField('Derivato da prenotazione', default=False, editable=False)

	""" Nel listare i viaggi, mostro solo quelli padre, con sottolistati i loro eventuali viaggi figli """

	class Meta:
		verbose_name_plural = _("Viaggi")
		permissions = (('change_oldviaggio', 'Cambia vecchio viaggio'), ('change_doppi', 'Cambia il numero di casette'))
		ordering = ("data_padre", "id_padre", "data", 'id')

	def url(self):
		return reverse("tamNuovaCorsaId", kwargs={"id": self.id})

	def __unicode__(self):
		result = u"%s da %s a %s." % (
		self.data.astimezone(tamdates.tz_italy).strftime("%d/%m/%Y %H:%M"), self.da, self.a)
		if self.cliente:
			result += u" Per %s:" % self.cliente
		else:
			result += u" Per privato:"
		result += u" %spax %s." % (self.numero_passeggeri, self.esclusivo and u"taxi" or u"collettivo")
		if self.conducente: result += u" Assegnato a %s." % self.conducente
		return result

	def descrizioneDivisioneClassifiche(self):
		""" Restituisco come il viaggio si divide nelle classifiche """
		return descrizioneDivisioneClassifiche(self)

	#	__changeableFieldsComputed=None
	#	def _getChangeableFields(self):
	#		if self.__changeableFieldsComputed is None:
	#			fields=[]
	#			for field in Viaggio._meta.fields:
	#				if field.editable:			# aggiungo in automatico tutti i campi modificabili
	#					fields.append(field.name)
	#			self.__changeableFieldsComputed=
	#			logging.debug("GET CHANGABLE FIELDS")
	#			logging.debug("%s" %self.__changeableFieldsComputed)
	#		return self.__changeableFieldsComputed
	#	changeableFields=property(_getChangeableFields)

	def updatePrecomp(self, doitOnFather=True, force_save=False, forceDontSave=False, numDoppi=None):
		""" Aggiorna tutti i campi precalcolati del viaggio.
			Se il tragitto è cambiato e il viaggio era già salvato lo aggiorna
			Se il viaggio ha un padre ricorre sul padre.
			Se il viaggio ha figli ricorre sui figli.
			numDoppi se è diverso da None forza al numero di doppi indicato
			con forceDontSave indico l'id che sto già salvando, e che non c'è bisogno di risalvare anche se cambia
		"""
		#print "updateprecomp:", self.id
		if doitOnFather and self.padre_id:
			#			logging.debug("Ricorro al padre di %s: %s" % (self.pk, self.padre.pk))
			self.padre.updatePrecomp(forceDontSave=forceDontSave)  # run update on father instead
			return
		changed = False

		# lista dei campi che vengono ricalcolati
		fields = [
			"html_tragitto",
			"prezzo_finale", "km",
			"prezzoVenezia", "prezzoPadova",
			"prezzoDoppioPadova",
			"punti_abbinata",
			"arrivo",
			"is_valid",
			"date_start",
		]

		oldValues = {}
		for field in fields:
			oldValues[field] = getattr(self, field)

		self.tratta = self._tratta()  # le tratte come prima cosa, sono richieste da tutti
		self.tratta_start = self._tratta_start()
		self.tratta_end = self._tratta_end()
		self.date_start = self._date_start()  # richiede tratta_start

		self.arrivo = self.is_arrivo()

		self.km = self.get_kmrow()  # richiede le tratte
		self.costo_sosta = Decimal(
			self.sostaFinaleMinuti()) * 12 / 60  # costo della sosta 12€/h, richiede tratte, usa _isabbinata e nexbro

		self.is_abbinata = self._is_abbinata()
		self.is_valid = self._is_valid()  # richiede le tratte

		forzaSingolo = (numDoppi is 0)
		self.prezzo_finale = self.get_value(forzaSingolo=forzaSingolo)  # richiede le tratte

		self.punti_diurni = self.punti_notturni = Decimal(0)  # Precalcolo i punti disturbo della corsa
		self.prezzoPadova = self.prezzoVenezia = self.prezzoDoppioPadova = 0
		self.punti_abbinata = self.prezzoPunti = 0
		process_classifiche(viaggio=self, force_numDoppi=numDoppi)

		self.html_tragitto = self.get_html_tragitto()

		for field in fields:
			if oldValues[field] != getattr(self, field):
				changed = True
				break

		if (changed and self.id and not forceDontSave) or force_save:
			self.save()

		if self.id:  # itero sui figli
			for figlio in self.viaggio_set.all():
				figlio.updatePrecomp(doitOnFather=False, numDoppi=numDoppi, forceDontSave=forceDontSave)

	def get_html_tragitto(self):
		""" Ritorna il tragitto da template togliendogli tutti gli spazi """
		tragitto = render_to_string('corse/dettagli_viaggio.inc.html', {"viaggio": self,
		                                                                "STATIC_URL": settings.STATIC_URL})
		tragitto = reallySpaceless(tragitto)
		return tragitto

	def save(self, *args, **kwargs):
		"""Ridefinisco il salvataggio dei VIAGGI per popolarmi i campi calcolati"""
		if 'updateViaggi' in kwargs:
			updateViaggi = kwargs['updateViaggi']
			del (kwargs['updateViaggi'])
		else:
			updateViaggi = True
		if not updateViaggi:
			return super(Viaggio, self).save(*args, **kwargs)

		if not self.conducente:  # quando confermo o richiedo un conducente DEVO avere un conducente
			self.conducente_confermato = False
			self.conducente_richiesto = False
		if self.conducente_richiesto:  # il conducente richiesto rende automaticamente il viaggio confermato
			self.conducente_confermato = True
		if not self.conducente_confermato:
			self.conducente = None
		if self.cliente:
			self.passeggero = None

		# inserisco data e ID del gruppo per gli ordinamenti
		self.id_padre = self.padre.id if self.padre_id is not None else self.id
		self.data_padre = self.padre.data if self.padre_id is not None else self.data

		logging.debug("Update di *%s*." % self.pk)
		#invalidate_template_cache("viaggio", self.id)
		super(Viaggio, self).save(*args, **kwargs)
		for figlio in self.viaggio_set.all():  # i figli ereditano dal padre
			changed = False
			if self.padre_id:  # tutti i figli hanno un solo padre, nessuna ricorsione
				figlio.padre = self.padre
				changed = True
			if figlio.conducente != self.conducente:  # il conducente è sempre quello del padre
				figlio.conducente = self.conducente
				changed = True
			if figlio.conducente_confermato != self.conducente_confermato:  #... e così la conferma
				figlio.conducente_confermato = self.conducente_confermato
				changed = True
			if changed:
				logging.debug("Update -> *%s*." % figlio.pk)
				figlio.save(*args, **kwargs)

	def delete_url(self):
		return reverse("tamCorsaIdDel", kwargs={"id": self.id})

	def is_arrivo(self):
		""" Return True if travel is an ARRIVO referring to luogo """
		#		logging.debug("is_arrivo")
		luogo = self.luogoDiRiferimento
		if not luogo: return False  # non ho un riferimento
		# aggiungo un tag ad ogni viaggio a seconda se è un arrivo o meno
		bacinoPredefinito = luogo.bacino

		if bacinoPredefinito:  # vengo da una zona
			return (bacinoPredefinito != self.da.bacino)  # mi muovo solo se sono fuori dalla zona
		else:  # vengo da un posto (non da una zona)
			return (luogo != self.da)  # mi muovo se il posto è diverso

	def _get_prefratello(self):
		""" Per i figli restituisco il fratello precedente (o il padre) """
		#		logging.debug("Trovo il pre fratello per %s"%self.id)
		if self.padre_id is None:
			return
		lastbro = self.padre
		for fratello in self.padre.viaggio_set.all():
			if fratello == self:
				break
			lastbro = fratello
		return lastbro

	prefratello = property(_get_prefratello)

	def nextfratello(self):
		""" Per le abbinate restituisco il prossimo fratello (Niente se è l'ultimo) """
		#		print "Trovo il next fratello per %d" % self.id
		if self.padre_id is None:
			if not self._is_abbinata(simpleOne=True):
				#				self.nextfratello = None
				self.cache_fratello = None
				return  # per i singoli ritorno None
			else:
				padre = self
		else:
			padre = self.padre
		lastbro = padre
		for fratello in padre.viaggio_set.all():
			if lastbro == self:
				#				self.nextfratello = fratello
				self.cache_fratello = fratello
				return fratello
			lastbro = fratello
		self.cache_fratello = None

	def lastfratello(self):
		""" Restituisco l'ultimo viaggio del gruppo """
		logging.debug("Trovo l'ultimo fratello per %s" % self.id)
		lastone = self
		if self.padre_id:  # vado al padre
			lastone = self.padre
		if lastone.viaggio_set.count() > 0:  # e scendo all'ultimo figlio
			lastone = list(lastone.viaggio_set.all())[-1]
		return lastone


	def _tratta_start(self):
		""" Restituisce la tratta dal luogo di riferimento all'inizio della corsa """
		#logging.debug("Trovo la tratta start %s" % self.id)
		if self.padre_id is None:  # per singoli o padri parto dal luogo di riferimento
			luogoDa = self.luogoDiRiferimento
			if luogoDa != self.da:
				return get_tratta(luogoDa, self.da)

	def _tratta(self):
		""" Normalmente è la tratta vera e propria, ma per le associazioni 	potrebbe essere una tratta intermedia, o addirittura essere nulla """
		#logging.debug("Trovo la tratta middle %s" % self.id)
		if self._is_abbinata() == "P":
			return None
		else:
			return get_tratta(self.da, self.a)

	def _tratta_end(self):
		""" Restituisce la tratta dal luogo di riferimento all'inizio della corsa """
		#logging.debug("Trovo la tratta end %s" % self.id)
		nextbro = self.nextfratello()
		if not nextbro:  # non ho successivi, riporto al luogoDiRiferimento
			da = self.a
			a = self.luogoDiRiferimento
		else:
			if self._is_abbinata() == "P":
				# sono un collettivo partenza: la tratta=None quindi vado dal mio iniziale all'iniziale prossimo
				da = self.da
				a = nextbro.da
			else:
				da = self.a
				a = nextbro.da
		if da != a:
			return get_tratta(da, a)

	def sostaFinale(self):
		nextbro = self.nextfratello()
		if nextbro:
			this_end = self.date_end()
			if nextbro.data <= this_end:
				return None
			else:
				return nextbro.data - this_end

	def sostaFinaleMinuti(self):
		sosta = self.sostaFinale()
		if sosta and sosta.seconds > 60:
			return int(sosta.seconds / 60)
		else:
			return 0


	def _date_start(self):
		""" Return the time to start to be there in time, looking Tratte
			if the start place is the same time is the time of the travel
		"""
		tratta_start = self.tratta_start
		anticipo = 0
		if tratta_start and tratta_start.is_valid():  # tratta iniziale
			anticipo += tratta_start.minuti
		if anticipo:
			return self.data - datetime.timedelta(minutes=anticipo)
		else:
			return self.data

	def date_end(self, recurse=False):
		""" Ritorno il tempo finale di tutta la corsa (compresi eventuali figli se recurse) """
		#		logging.debug("Data finale di %s. Recurse:%s"%(self.id, recurse))
		if not recurse or not self.id:  # se devo ancora salvare non cerco figli
			ultimaCorsa = self  # trovo il tempo finale solo di me stesso
		else:
			ultimaCorsa = self.lastfratello()  # trovo il tempo finale dell'ULTIMA corsa

		tratta = ultimaCorsa.tratta
		tratta_end = ultimaCorsa.tratta_end
		end_time = ultimaCorsa.data
		#		logging.debug("Partiamo da %s"%end_time)

		# quando parto da un aeroporto la corsa dura 30 minuti di più
		# non quando sono in sosta, arrivato in un aereoporto, in modo che i 30 minuti in più siano alla ripartenza
		if ultimaCorsa.da.speciale == 'A' and tratta:
			end_time += datetime.timedelta(minutes=30)

		if tratta and tratta.is_valid():  # add the runtime of this tratta
			#			logging.debug("Aggiungo %s per la tratta %s" %(tratta.minuti, tratta))
			end_time += datetime.timedelta(minutes=tratta.minuti)
		if tratta_end and tratta_end.is_valid():
			#			logging.debug("Aggiungo %s per la tratta %s" %(tratta_end.minuti, tratta_end))
			end_time += datetime.timedelta(minutes=tratta_end.minuti)
		#		logging.debug("Tempo finale: %s "%end_time)
		return end_time


	def trattaInNotturna(self):
		""" Restituisce True se la sola tratta considerata (non i figli e non le pre_tratte post_tratte
		 sono in fascia [22-6) """
		start = self.data
		tratta = self._tratta()
		if tratta:
			end = self.data + datetime.timedelta(minutes=tratta.minuti)
		else:
			end = self.data
		inizioNotte = start.replace(hour=22, minute=0)
		if start.hour < 6: inizioNotte -= datetime.timedelta(days=1)
		fineNotte = end.replace(hour=6, minute=0)
		if fineNotte < inizioNotte: fineNotte += datetime.timedelta(days=1)
		result = False
		if start <= inizioNotte and end >= inizioNotte: result = True
		if start < fineNotte and end >= fineNotte: result = True
		if start >= inizioNotte and end <= fineNotte: result = True
		#		if start.hour> and end.hour>22: return result
		return result

	def disturbi(self, date_start=None, date_end=None):
		""" Restituisce un dizionario di "codiceFascia":punti con le fasce e i punti disturbo relativi.
			Ho due fasce mattutine 4-6, 6-7:45 di due e un punto
			due fasce serali 20-22:30, 22:30-4
			a due a due hanno lo stesso codice prefissato con la data in cui la fascia comincia
			Il disturbo finale per una fascia è il massimo del valore di tutte le se sottofascie componenti
		"""
		if self.conducente_richiesto:
			return {}
		if self.date_start < tamdates.date_enforce(datetime.datetime(2012, 3, 1)):
			metodo = fasce_uno_due
		else:
			metodo = getattr(settings, "METODO_FASCE", fasce_semilineari)
		return trovaDisturbi(self.date_start, self.date_end(recurse=True), metodo=metodo)

	# def aggiungi_fascia(h_start, min_start, h_end, m_end, points, fasciaKey):
	# 	""" Aggiungo a result il codice della fascia con la data prefissata e i punti indicati se
	# 		la corsa tra date_start e date_end tocca nel giorno indicato da dayMarker tra le ore h_start:m_start e h_end:m_end
	# 		Controllo se date_start cade nella fascia per contarlo
	# 		o se date_end è nella fascia
	# 		o se date_start è prima della fascia e date_end è dopo
	# 	"""
	# 	fascia_start = dayMarker.replace(hour=h_start, minute=min_start)
	# 	fascia_end = dayMarker.replace(hour=h_end, minute=m_end)
	# 	if fascia_start <= date_start < fascia_end or \
	# 	fascia_start < date_end <= fascia_end or \
	# 	(date_start < fascia_start and date_end > fascia_end):
	# 		#print "mi disturba [%d] la fascia %s" % (points, fasciaKey)
	# 		result[fasciaKey] = max(result.get(fasciaKey), points)
	#
	# if date_start is None: date_start = self.date_start
	# if date_end is None: date_end = self.date_end(recurse=True)
	# #print "Disturbo dalle %s alle %s" % (date_start, date_end)
	# dayMarker = date_start.replace()   # creo una copia
	# #daymaker mi serve per scorrere tra i giorni, partendo da quello di date_start al giorno di arrivo
	# result = {}
	# while dayMarker.date() <= date_end.date():
	# 	# fino alle 4:00 sono 2 punti notturni, ma assegnati con chiave al giorno precedente
	# 	aggiungi_fascia(0, 0, 4, 1, points=2,
	# 					fasciaKey=((dayMarker - datetime.timedelta(days=1)).strftime("%d/%m/%Y"), "night"))
	# 	aggiungi_fascia(4, 1, 6, 1, points=2,
	# 					fasciaKey=(dayMarker.strftime("%d/%m/%Y"), "morning")) # alle 6:00 sono 2 punto diurno
	# 	aggiungi_fascia(6, 1, 7, 46, points=1,
	# 					fasciaKey=(dayMarker.strftime("%d/%m/%Y"), "morning"))	# 7:45 comprese l'ultimo disturbo
	# 	if dayMarker.isoweekday() in (6, 7):	   # saturday and sunday, normal worktime is less
	# 		aggiungi_fascia(20, 0, 22, 31, points=1,
	# 						fasciaKey=(dayMarker.strftime("%d/%m/%Y"), "night"))
	# 	else:
	# 		aggiungi_fascia(20, 30, 22, 31, points=1,
	# 						fasciaKey=(dayMarker.strftime("%d/%m/%Y"), "night"))
	# 	aggiungi_fascia(22, 31, 23, 59, points=2,
	# 					fasciaKey=(dayMarker.strftime("%d/%m/%Y"), "night"))
	# 	dayMarker = dayMarker + datetime.timedelta(days=1)	# passa il giorno
	# return result

	def get_kmrow(self):
		""" Restituisce il N° di KM totali di corsa con andata, corsa e ritorno """
		tratta_start = self._tratta_start()
		tratta = self._tratta()
		tratta_end = self._tratta_end()
		result = 0
		if tratta_start: result += tratta_start.km
		if tratta: result += tratta.km
		if tratta_end: result += tratta_end.km
		return result

	def get_kmtot(self):
		""" Restituisce il N° di KM totali di corsa con andata, corsa, figli e ritorno """
		result = self.get_kmrow()
		if self.id is None: return result
		for figlio in self.viaggio_set.all():
			result += figlio.get_kmrow()
		return result

	def _is_collettivoInPartenza(self):
		"""	Vero se questo viaggio va dalla partenza alla partenza del fratello successivo.
			Assieme si andrà  ad una destinazione comune
		"""
		#		logging.debug("Is collettivo in partenza %s" %self.id)
		nextbro = self.nextfratello()
		if nextbro and nextbro.da == self.a:  # se il successivo parte da dove arrivo è sicuramente un collettivo in successione
			return False
		if nextbro and nextbro.data < \
						self.data + datetime.timedelta(
						minutes=get_tratta(self.da, self.a).minuti + (30 if self.da.speciale == "A" else 0)):
			# tengo conto che questa corsa dura 30 minuti in più se parte da un aereoporto
			#			logging.debug("%s e' prima delle %s" % (nextbro.id, self.data+datetime.timedelta(minutes=get_tratta(self.da, self.a).minuti*0.5)) )
			return True
		else:
			return False

	def _is_abbinata(self, simpleOne=False):
		""" True se la corsa un'abbinata (padre o figlio)
			se simpleOne==False controllo anche le differenze tra abbinata in Successione e abbinata in Partenza
		"""
		#print("Abbinata? %s" % self.id)
		if self.id is None: return False  # prima di salvare non sono un'abbinata (viaggio_set.count() mi darebbe tutte le corse
		if self.padre_id or self.viaggio_set.count() > 0:
			if simpleOne: return True
			if self._is_collettivoInPartenza():
				self.cache_isabbinata = 'P'
				return "P"  # collettivo in partenza
			else:
				self.cache_isabbinata = 'S'
				return "S"  # abbinata
		else:
			return ""  # non abbinata

	def is_long(self):
		""" Ritorna vero se la tratta, andando e tornando è lunga """
		return self.km >= getattr(settings, 'KM_PER_LUNGHE', 50)

	def is_medium(self):
		""" Ritorna vero se la tratta è media """
		return 25 <= self.km < getattr(settings, 'KM_PER_LUNGHE', 50) or (self.km < 25 and self.prezzo > 16)

	def _is_valid(self):
		"""Controlla che il viaggio abbia tutte le tratte definite"""
		tratta_start = self.tratta_start
		tratta = self.tratta
		tratta_end = self.tratta_end
		if (tratta_start is None or tratta_start.is_valid()) and (tratta is None or tratta.is_valid()) and (
				tratta_end is None or tratta_end.is_valid()):
			return True
		else:
			return False

	def vecchioConfermato(self):
		return self.conducente_confermato and self.date_start < tamdates.ita_now().replace(hour=0, minute=0)

	def prezzo_commissione(self):
		""" Restituisce il valore in euro della commissione """
		if not self.commissione:
			return 0
		else:
			if self.tipo_commissione == "P":
				return self.prezzo * (self.commissione / Decimal(100))  # commissione in percentuale
			else:
				return self.commissione

	def get_value(self, forzaSingolo=False):
		""" Return the value of this trip on the scoreboard """
		return process_value(self, forzaSingolo=forzaSingolo)

	def get_valuetot(self, forzaSingolo=False):
		result = self.get_value()
		for figlio in self.viaggio_set.all():
			result += figlio.get_value()
		return result

	def lordo(self):
		""" Il lordo vero e proprio """
		result = self.prezzo
		for figlio in self.viaggio_set.all():
			result += figlio.prezzo
		return result

	def get_lordotot(self):
		""" Restituisce il lordo, tolto di autostrada e commissione """
		result = self.prezzo - self.costo_autostrada - self.prezzo_commissione()
		#		logging.debug("Corsa padre: %s" % result )
		for figlio in self.viaggio_set.all():
			#			logging.debug("	 figlio: %s" % (figlio.prezzo - figlio.costo_autostrada - figlio.prezzo_commissione()) )
			result += figlio.prezzo - figlio.costo_autostrada - figlio.prezzo_commissione()
		return result

	def costo_autostrada_default(self):
		""" Restituisce il costo totale dell'autostrada, in modo da suggerirlo """
		#print "Ricalcolo autostrada per %d" % self.pk    #TMP:
		tratta_start = self._tratta_start()
		tratta = self._tratta()
		tratta_end = self._tratta_end()
		result = 0
		if tratta_start:
			#print tratta_start.da, tratta_start.a
			result += tratta_start.costo_autostrada
		if tratta:
			#print tratta.da, tratta.a
			result += tratta.costo_autostrada
		if tratta_end:
			#print tratta_end.da, tratta_end.a
			result += tratta_end.costo_autostrada
		return result

	def confirmed(self):
		""" True se il conducente è confermato... nel qual caso poi lo conto in classifica """
		return self.conducente_confermato

	def warning(self):
		""" True se la corsa va evidenziata perché non ancora confermata se manca poco alla partenza """
		return (not self.conducente_confermato
		        and (self.date_start - datetime.timedelta(hours=2) < tamdates.ita_now())
		)

	def get_classifica(self, classifiche=None, conducentiPerCapienza=None):
		conducenti = []
		inattivi = []
		# print "getclassifica", self

		if classifiche is None:
			classifiche = get_classifiche()
		classid = {}
		for classifica in classifiche:  # metto le classifiche in un dizionario
			#id = classifica["conducente_id"]
			classid[classifica["conducente_id"]] = classifica

		# cache conducenti per capienza ******************************************************
		if self.numero_passeggeri in conducentiPerCapienza:
			conducentiConCapienza = conducentiPerCapienza[self.numero_passeggeri]
		#print "Uso la cache per conducenti con capienza %d" % self.numero_passeggeri
		else:
			# Metto in cache la lista dei clienti che possono portare almeno X persone
			conducentiConCapienza = Conducente.objects.filter(max_persone__gte=self.numero_passeggeri)
			#print "Imposto la cache conducenti con capienza %d" % self.numero_passeggeri
			conducentiPerCapienza[self.numero_passeggeri] = conducentiConCapienza
		# ************************************************************************************

		#		# cache conducenti per capienza GLOBAL STYLE******************************************
		#		global cache_conducentiPerPersona
		#		if self.numero_passeggeri in cache_conducentiPerPersona:
		#			conducentiConCapienza = cache_conducentiPerPersona[self.numero_passeggeri]
		#			#print "Uso la cache per conducenti con capienza %d" % self.numero_passeggeri
		#		else:
		#			# Metto in cache la lista dei clienti che possono portare almeno X persone
		#			conducentiConCapienza = Conducente.objects.filter(max_persone__gte=self.numero_passeggeri)
		#			print "Imposto la cache conducenti con capienza %d" % self.numero_passeggeri
		#			cache_conducentiPerPersona[self.numero_passeggeri] = conducentiConCapienza
		#		# ************************************************************************************

		if 'calendariopresenz' in settings.INSTALLED_APPS:
			calendarizzati = Calendar.objects.filter(
				date_start__lt=self.date_end,  # I use the date-interval cross detection
				date_end__gt=self.date_start,
			)
			c_byid = {}
			for calendario in calendarizzati:
				cid = calendario.conducente.id
				c_byid[cid] = c_byid.get(cid, []) + [calendario.type]
			viaggi_contemporanei = Viaggio.objects.filter(
				date_start__lt=self.date_end,  # I use the date-interval cross detection
				date_end__gt=self.date_start,
				conducente_confermato=True,
			)
			for viaggio in viaggi_contemporanei:
				cid = viaggio.conducente.id
				c_byid[cid] = c_byid.get(cid, []) + ['in viaggio']
			print c_byid

		for conducente in conducentiConCapienza:  # listo i conducenti attivi che parteciperanno
			if conducente.attivo is False:
				inattivi.append(conducente)
			else:
				# if not classid.has_key(conducente.id):
				# 	# il conducente è nuovo, senza viaggi. Classifica alternativa con solo gli iniziali
				# 	classid[conducente.id] = {
				# 	"id": conducente.id,
				# 	"conducente_nick": conducente.nick,
				# 	"max_persone": conducente.max_persone,
				# 	"puntiDiurni": conducente.classifica_iniziale_diurni,
				# 	"puntiNotturni": conducente.classifica_iniziale_notturni,
				# 	"prezzoVenezia": conducente.classifica_iniziale_long,
				# 	"prezzoPadova": conducente.classifica_iniziale_medium,
				# 	"prezzoDoppioPadova": conducente.classifica_iniziale_doppiPadova,
				# 	"punti_abbinata": conducente.classifica_iniziale_puntiDoppiVenezia
				# 	}
				chiave = []
				# da priorità alle classifiche così come nei settings

				keys = []
				for desc_classifica in settings.CLASSIFICHE:
					punti_viaggio = getattr(self, desc_classifica['viaggio_field'])
					if punti_viaggio:
						ignore_if_field = desc_classifica.get('ignore_if_field', None)
						if ignore_if_field is not None and getattr(self, ignore_if_field):
							# print "ho punti in %s, salto %s" % (ignore_if_field, desc_classifica['mapping_field'])
							continue
						chiave.append(classid[conducente.id][desc_classifica['mapping_field']])
						keys.append(desc_classifica['mapping_field'])

				# print self, chiave
				# if self.punti_diurni: chiave.append(classid[conducente.id]["puntiDiurni"])
				# if self.punti_notturni: chiave.append(classid[conducente.id]["puntiNotturni"])
				# if self.punti_abbinata: chiave.append(classid[conducente.id]["punti_abbinata"])
				# if self.prezzoVenezia: chiave.append(classid[conducente.id]["prezzoVenezia"])
				# if self.prezzoDoppioPadova: chiave.append(classid[conducente.id]["prezzoDoppioPadova"])
				# if self.prezzoPadova: chiave.append(classid[conducente.id]["prezzoPadova"])

				chiave.append(conducente.nick)  # nei parimeriti metto i nick in ordine

				conducenti.append((chiave, conducente))
		conducenti.sort()
		return [c[1] for c in conducenti] + inattivi

	def punti_notturni_interi_list(self):
		return range(int(self.punti_notturni))

	def punti_notturni_quarti(self):
		""" Restituisce la parte frazionaria dei notturni """
		return self.punti_notturni % 1

	def punti_diurni_interi_list(self):
		return range(int(self.punti_diurni))

	def punti_diurni_quarti(self):
		""" Restituisce la parte frazionaria dei notturni """
		return self.punti_diurni % 1

	def incidenza_prezzo_sosta(self):
		""" Stringa che aggiungo alla descrizione dei prezzi per indicare che la sosta viene scontata """
		if settings.SCONTO_SOSTA:
			return "al %d%%" % (100 - settings.SCONTO_SOSTA)
		else:
			return ""

	def incidenza_differto(self):
		""" Stringa che aggiungo alla descrizione dei prezzi per indicare che il prezzo viene scontato perché differto """
		if settings.SCONTO_FATTURATE:
			return "- p%d%%" % settings.SCONTO_FATTURATE
		else:
			return ""

	def prezzo_netto(self, iva=10):
		if PREZZO_VIAGGIO_NETTO:
			return self.prezzo
		else:
			return self.prezzo * 100 / (100 + iva)


class Conducente(models.Model):
	""" I conducuenti, ogni conducente avrà la propria classifica, ed una propria vettura.
		Ogni conducente può essere in servizio o meno.
	"""
	nome = models.CharField("Nome", max_length=40, unique=True)
	dati = models.TextField(null=True, blank=True, help_text='Stampati nelle fattura conducente')
	nick = models.CharField("Sigla", max_length=5, blank=True, null=True)
	max_persone = models.IntegerField(default=4)
	attivo = models.BooleanField(default=True, db_index=True)
	emette_ricevute = models.BooleanField("Emette senza IVA?",
	                                      help_text="Il conducente può emettere fatture senza IVA?", default=True)
	assente = models.BooleanField(default=False)

	classifica_iniziale_diurni = models.DecimalField("Supplementari diurni", max_digits=12, decimal_places=2, default=0)
	classifica_iniziale_notturni = models.DecimalField("Supplementari notturni", max_digits=12, decimal_places=2,
	                                                   default=0)

	classifica_iniziale_puntiDoppiVenezia = models.IntegerField("Punti Doppi Venezia", default=0)
	classifica_iniziale_prezzoDoppiVenezia = models.DecimalField("Valore Doppi Venezia", max_digits=12,
	                                                             decimal_places=2, default=0)  # fino a 9999.99
	classifica_iniziale_doppiPadova = models.DecimalField("Doppi Padova", max_digits=12, decimal_places=2,
	                                                      default=0)  # fino a 9999.99

	classifica_iniziale_long = models.DecimalField("Venezia", max_digits=12, decimal_places=2,
	                                               default=0)  # fino a 9999.99
	classifica_iniziale_medium = models.DecimalField("Padova", max_digits=12, decimal_places=2,
	                                                 default=0)  # fino a 9999.99

	class Meta:
		verbose_name_plural = _("Conducenti")
		ordering = ["-attivo", "nick", "nome"]
		permissions = (('change_classifiche_iniziali', 'Cambia classifiche iniziali'),)

	def save(self, *args, **kwargs):
		#global cache_conducentiPerPersona
		#cache_conducentiPerPersona = {}	# cancello la cache dei conducenti con capienza
		cache.delete('conducentiPerPersona')
		super(Conducente, self).save(*args, **kwargs)

	def __unicode__(self):
		if self.nick:
			return self.nick
		else:
			return self.nome

	def __repr__(self):
		return self.__unicode__()

	def delete_url(self):
		return reverse("tamConducenteIdDel", kwargs={"id": self.id})

	def url(self):
		return reverse("tamConducenteId", kwargs={"id": self.id})

	def ricevute(self):
		""" Ritorno le ricevute emesse da questo conducente """
		from fatturazione.models import Fattura

		ricevute = Fattura.objects.filter(tipo='3', righe__conducente=self)
		return ricevute.distinct()


class Cliente(models.Model):
	""" Ogni cliente ha le sue caratteristiche, ed eventualmente un suo listino """
	nome = models.CharField("Nome cliente", max_length=40, unique=True)
	dati = models.TextField(null=True, blank=True, help_text='Stampati nelle fattura conducente')
	tipo = models.CharField("Tipo cliente", max_length=1, choices=TIPICLIENTE)
	fatturazione = models.BooleanField("Fatturazione richiesta", default=False)
	pagamento_differito = models.BooleanField("Fatturazione esente IVA", default=False)
	incassato_albergo = models.BooleanField("Conto fine mese", default=False)
	listino = models.ForeignKey("Listino", verbose_name="Listino cliente", null=True, blank=True)
	commissione = models.DecimalField("Quota consorzio", max_digits=9, decimal_places=2, default=0)  #fissa in euro
	tipo_commissione = models.CharField("Tipo di quota", max_length=1, choices=TIPICOMMISSIONE, default="F")
	attivo = models.BooleanField(default=True)
	note = models.TextField(null=True, blank=True)

	class Meta:
		verbose_name_plural = _("Clienti")
		ordering = ["nome"]

	def __unicode__(self):
		if self.nome.strip():
			result = self.nome
		else:
			result = "(nessun nome)"
		if not self.attivo:
			result += "(inattivo)"
		return result

	def icon(self):
		""" Ritorno l'icona associata al tipo cliente """
		return staticfiles_storage.url('tipiCliente/%s.png' % self.tipo)


	def url(self):
		return reverse("tamClienteId", kwargs={"id_cliente": self.id})

	def save(self, *args, **kwargs):
		if self.nome.lower() == "privato":
			raise Exception("Scusa ma non puoi chiamarlo PRIVATO... è un nome riservato")
		super(Cliente, self).save(*args, **kwargs)


class Passeggero(models.Model):
	""" I passeggeri sono clienti particolari con meno caratteristiche """
	nome = models.CharField(max_length=40, unique=True)
	dati = models.TextField(null=True, blank=True)

	class Meta:
		verbose_name_plural = _("Passeggeri")
		ordering = ["nome"]
		permissions = (('fastinsert_passenger', 'Inserimento passeggero veloce'),)

	def __unicode__(self):
		return self.nome

	def delete_url(self):
		return reverse("tamPrivatoIdDel", kwargs={"id": self.id})

	def url(self):
		return reverse("tamPrivatoId", kwargs={"id": self.id})


class Listino(models.Model):
	""" Ogni listino ha un suo nome ed una serie di tratte collegate.
		È indipendente dal cliente.
	"""
	nome = models.CharField(max_length=30, unique=True)

	class Meta:
		verbose_name_plural = _("Listini")
		ordering = ["nome"]

	def __unicode__(self):
		return self.nome

	def get_prezzo(self, da, a, tipo_servizio="T", pax=3, tryReverse=True):
		""" Cerca il prezzo del listino DA-A o A-DA, e restituisce None se non esiste """
		prezziDiretti = self.prezzolistino_set.filter(tratta__da=da, tratta__a=a, max_pax__gte=pax,
		                                              tipo_servizio=tipo_servizio)
		choosenResult = None  # scelgo il prezzo adeguato con meno passeggeri max
		for prezzoPossibile in prezziDiretti:
			if choosenResult:
				if prezzoPossibile.max_pax < choosenResult.max_pax: choosenResult = prezzoPossibile
			else:
				choosenResult = prezzoPossibile
		if choosenResult: return choosenResult
		if tryReverse:
			return self.get_prezzo(a, da, tipo_servizio, pax, tryReverse=False)  # provo a tornare il prezzo inverso


class PrezzoListino(models.Model):
	""" Ogni tratta del listino ha due prezzi, una per la fascia diurna e una per la fascia notturna """
	listino = models.ForeignKey(Listino)
	tratta = models.ForeignKey(Tratta)
	prezzo_diurno = models.DecimalField(max_digits=9, decimal_places=2, default=10)  # fino a 9999.99
	prezzo_notturno = models.DecimalField(max_digits=9, decimal_places=2, default=10)  # fino a 9999.99

	commissione = models.DecimalField("Quota consorzio", max_digits=9, decimal_places=2, null=True,
	                                  default=0)  #fissa in euro
	tipo_commissione = models.CharField("Tipo di quota", max_length=1, choices=TIPICOMMISSIONE, default="F")
	ultima_modifica = models.DateField(auto_now=True)

	tipo_servizio = models.CharField(choices=TIPISERVIZIO, max_length=1, default="T")  # Collettivo o Taxi
	max_pax = models.IntegerField("Pax Massimi", default=4)

	flag_fatturazione = models.CharField("Fatturazione forzata",
	                                     max_length=1,
	                                     choices=[('S', 'Fatturazione richiesta'),
	                                              ('N', 'Fatturazione non richiesta'),
	                                              ('-', 'Usa impostazioni del cliente'),
	                                     ],
	                                     default='-',
	                                     blank=False, null=False,
	)

	class Meta:
		verbose_name_plural = _("Prezzi Listino")
		unique_together = (("listino", "tratta", "tipo_servizio", "max_pax"),)
		ordering = ["tipo_servizio", "max_pax"]

	#		order_with_respect_to="tratta"

	def stringa_dettaglio(self):
		if self.tipo_servizio == "C":
			return "collettivo fino a %d pax" % self.max_pax
		else:
			return "taxi fino a %d pax" % self.max_pax


	def __unicode__(self):
		result = u"%s. Da %s a %s. %s [%s] " % (
		self.listino, self.tratta.da, self.tratta.a, self.prezzo_diurno, self.prezzo_notturno)
		if self.commissione:
			if self.tipo_commissione == "P":
				result += u"con quota del %d%% " % (self.commissione)
			else:
				result += u"con quota di %d€ " % self.commissione
		result += self.stringa_dettaglio()
		return result


class ProfiloUtente(models.Model):
	user = models.ForeignKey(User, unique=True, editable=False)
	luogo = models.ForeignKey(Luogo, verbose_name="Luogo di partenza", null=True, blank=True)

	class Meta:
		permissions = (('can_backup', 'Richiede un backup'), ('get_backup', 'Scarica un backup'))
		verbose_name_plural = _("Profili utente")

	def __unicode__(self):
		return "%s" % self.user


class Conguaglio(models.Model):
	""" Memorizza tutti i conguagli effettuati tra i conducenti """
	data = models.DateTimeField(auto_now=True)
	conducente = models.ForeignKey(Conducente)
	dare = models.DecimalField(max_digits=9, decimal_places=2, default=10)  # fino a 9999.99

	class Meta:
		verbose_name_plural = _("Conguagli")

	def __unicode__(self):
		return "%s, %s: %s" % (self.data, self.conducente, self.dare)


def get_classifiche():
	"""	Restituisco le classifiche globali (per le corse confermate)
		Restituisce una lista di dizionari, ognuna con i valori del conducente.
		Utilizzo una query fuori dall'ORM di Django per migliorare le prestazioni.
	"""
	#	logging.debug("Ottengo le classifiche globali.")
	cursor = connections['default'].cursor()
	query = """
		select
			c.id as conducente_id, c.nick as conducente_nick, c.max_persone as max_persone,
			coalesce(sum("punti_diurni"),0)+classifica_iniziale_diurni as "puntiDiurni",
			coalesce(sum(punti_notturni),0)+classifica_iniziale_notturni as "puntiNotturni",
			coalesce(sum("prezzoVenezia"),0) + classifica_iniziale_long as "prezzoVenezia",
			coalesce(sum("prezzoPadova"),0) + classifica_iniziale_medium as "prezzoPadova",
			coalesce(sum("prezzoDoppioPadova"),0) + "classifica_iniziale_doppiPadova" as "prezzoDoppioPadova",
			coalesce(sum("punti_abbinata"),0) + "classifica_iniziale_puntiDoppiVenezia" as punti_abbinata
		from tam_conducente c
			left join tam_viaggio v on c.id=v.conducente_id and v.conducente_confermato
		where c.attivo --and c.nick='2'
			and not coalesce(v.annullato, false)
		group by c.id, c.nick
		order by conducente_nick
	"""
	cursor.execute(query, ())
	results = cursor.fetchall()

	classifiche = []
	fieldNames = [field[0] for field in cursor.description]
	for classifica in results:
		classDict = {}
		for name, value in zip(fieldNames, classifica):
			classDict[name] = value
		classifiche.append(classDict)
	return classifiche

# Comincia a loggare i cambiamenti a questi Modelli
from modellog.actions import startLog, stopLog

models_to_log = (Viaggio, Cliente, Passeggero,
                 Conducente, Tratta, PrezzoListino)


def startAllLog():
	for Model in models_to_log:
		startLog(Model)


def stopAllLog():
	for Model in models_to_log:
		stopLog(Model)


startAllLog()

# l'import di classifiche deve stare in fondo per evitare loop di importazione
from tam.views.classifiche import descrizioneDivisioneClassifiche

process_classifiche = settings.PROCESS_CLASSIFICHE_FUNCTION
process_value = settings.GET_VALUE_FUNCTION

PREZZO_VIAGGIO_NETTO = getattr(settings, 'PREZZO_VIAGGIO_NETTO', True)

# load models required for the tasks
from tam.tasks import TaskBackup, TaskMovelog, TaskArchive  # @UnusedImport
