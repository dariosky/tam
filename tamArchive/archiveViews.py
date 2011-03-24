#coding: utf-8
import datetime
import time
from decimal import Decimal
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
import logging
from django.db import transaction
#from django.db import connection
from django.db.models import Q
from tam.models import Viaggio, ActionLog, ProfiloUtente, stopLog, startLog, Conducente, \
	get_classifiche
from tamArchive.models import ViaggioArchive
from tam.views import SmartPager
from tam.models import logAction
from django.utils.datastructures import SortedDict # there are Python 2.4 OrderedDict, I use django to relax requirements

archiveNotBefore_days = 365

def menu(request, template_name="archive/menu.html"):
	dontHilightFirst = True
	if not request.user.has_perm('tamArchive.archive') and not request.user.has_perm('tamArchive.flat'):
		request.user.message_set.create(message=u"Devi avere accesso o all'archiviazione o all'appianamento.")
		return HttpResponseRedirect(reverse("tamUtil"))

	class ArchiveForm(forms.Form):
		""" Form che chiede una data non successiva a 30 giorni fa """
		class Media:
			css = {
				'all': ('js/jquery.ui/themes/ui-lightness/ui.all.css',)
			}
			js = ('js/jquery.min.js', 'js/jquery.ui/jquery-ui.custom-min.js', 'js/calendarPreferences.js')

		end_date_suggested = (datetime.date.today() - datetime.timedelta(days=archiveNotBefore_days)).replace(month=1, day=1).strftime('%d/%m/%Y')
		end_date = forms.DateField(
								   label="Data finale",
								   input_formats=[_('%d/%m/%Y')],
								   initial=end_date_suggested
								   )

	form = ArchiveForm()

	return render_to_response(template_name,
			{
				"dontHilightFirst": dontHilightFirst,
				"form": form,
			}
			, context_instance=RequestContext(request))


def vacuum_db(using='default'):
	from django.db import connections
	cursor = connections[using].cursor()
	logging.debug("Vacuum [%s]" % using)
	cursor.execute("VACUUM")
	transaction.set_dirty(using=using)

def archiveFromViaggio(viaggio):
	""" Crea una voce di archivio dato un viaggio """
	voceArchivio = ViaggioArchive(
			data=viaggio.data,
			da=viaggio.da,
			a=viaggio.a,
			path=viaggio.html_tragitto,
			pax=viaggio.numero_passeggeri,
			flag_esclusivo=viaggio.esclusivo,
			conducente="%s" % viaggio.conducente,
			flag_richiesto=viaggio.conducente_richiesto,
			cliente=(viaggio.cliente and viaggio.cliente.nome) or (viaggio.passeggero and viaggio.passeggero.nome),
			prezzo=viaggio.prezzo,
			prezzo_detail=render_to_string('corse/corse_prezzo_viaggio.inc.html', {"viaggio": viaggio, "nolink":True}),
			flag_fineMese=viaggio.incassato_albergo,
			flag_fatturazione=viaggio.fatturazione,
			flag_cartaDiCredito=viaggio.cartaDiCredito,
			flag_pagamentoDifferito=viaggio.pagamento_differito,
			numero_pratica=viaggio.numero_pratica,
			flag_arrivo=viaggio.arrivo,
			punti_abbinata=viaggio.punti_abbinata,
			note=viaggio.note,
		)
	return voceArchivio

def daRicordareDelViaggio(ricordi, viaggio):
	""" Ricorda quello che serve dalle classifiche di un viaggio """
	conducente_id = viaggio.conducente.id
	ricordiConducente = ricordi.get(conducente_id, {})
	campiMemoria = ('punti_diurni', 'punti_notturni', 'prezzoVenezia', 'prezzoPadova',
				'prezzoDoppioPadova', 'punti_abbinata')
	for nome_campo in campiMemoria:
		esistente = ricordiConducente.get(nome_campo, 0)
		ricordiConducente[nome_campo] = esistente + getattr(viaggio, nome_campo)
	ricordi[conducente_id] = ricordiConducente
	return ricordi

@transaction.commit_manually(using="archive")
def action(request, template_name="archive/action.html"):
	""" Archivia le corse, mantenendo le classifiche inalterate """
	if not request.user.has_perm('tamArchive.archive'):
		request.user.message_set.create(message=u"Devi avere accesso all'archiviazione.")
		return HttpResponseRedirect(reverse("tamArchiveUtil"))
	
	end_date_string = request.POST.get("end_date")
	try:
		timetuple = time.strptime(end_date_string, '%d/%m/%Y')
		end_date = datetime.date(timetuple.tm_year, timetuple.tm_mon, timetuple.tm_mday)
	except:
		end_date = None
	if (end_date is None) or end_date > (datetime.date.today() - datetime.timedelta(days=archiveNotBefore_days)):
		request.user.message_set.create(message=u"Devi specificare una data valida per archiviare.")
		return HttpResponseRedirect(reverse("tamArchiveUtil"))

	# non archivio le non confermate

	filtroViaggi = Q(data__lt=end_date, conducente__isnull=False, padre__isnull=True)
	archiveCount = Viaggio.objects.filter(data__lt=end_date, conducente__isnull=False).count()

	logDaEliminare = ActionLog.objects.filter(data__lt=end_date)
	logCount = logDaEliminare.count()
	archive_needed = archiveCount and logCount

	if "archive" in request.POST:
		viaggiDaArchiviare = Viaggio.objects.select_related("da", "a", "cliente", "conducente", "passeggero").order_by().filter(filtroViaggi)
			# Optimizations: mi faccio dare solo i modelli che mi interessano
			# Rimovo l'ordinamento di default
		logAction("K",
					instance=request.user,
					description="Archiviazione fino al %s" % end_date,
					user=request.user)
		logging.debug("Effettuo l'archiviazione fino al %s" % end_date)
		archiviati = 0
		lastArchiveNotify = 0
		stopLog(Viaggio)	# disabilita il log delle operazionni sul viaggio
		stopLog(Conducente)
		ricordi = {}	# ricordi[conducente_id] = {chiaveClassifica=valore}
		for viaggio in viaggiDaArchiviare:
			archiviati += 1

			viaggioArchiviato = archiveFromViaggio(viaggio)
			daRicordareDelViaggio(ricordi, viaggio)
			viaggioArchiviato.save()

			for figlio in viaggio.viaggio_set.select_related("da", "a", "cliente", "conducente", "passeggero").order_by().all():
				viaggioArchiviatoFiglio = archiveFromViaggio(figlio)
				viaggioArchiviatoFiglio.padre = viaggioArchiviato
				daRicordareDelViaggio(ricordi, figlio)
				viaggioArchiviatoFiglio.save()
				archiviati += 1

			if archiviati > 400:
#				transaction.commit(using='archive')
				for conducente_id, classifica in ricordi.items():
					conducente = Conducente.objects.get(pk=conducente_id)
					conducente.classifica_iniziale_diurni += classifica['punti_diurni']
					conducente.classifica_iniziale_notturni += classifica['punti_notturni']

					conducente.classifica_iniziale_long += classifica['prezzoVenezia']
					conducente.classifica_iniziale_medium += classifica['prezzoPadova']
					conducente.classifica_iniziale_doppiPadova += classifica['prezzoDoppioPadova']
					conducente.classifica_iniziale_puntiDoppiVenezia += classifica['punti_abbinata']
					conducente.save()

				ricordi = {}
#				assert(False)	#TMP: faccio solo i primi

			if archiviati >= lastArchiveNotify + 500:
				logging.debug("Effettuo il commit [%d]" % archiviati)
				lastArchiveNotify = archiviati
				transaction.commit(using='archive')
#				assert(False)	#TMP

		if lastArchiveNotify != archiviati:
			logging.debug("Effettuo il commit [%d]" % archiviati)
			transaction.commit(using='archive')

		logging.debug("Cancello tutti i viaggi appena archiviati")
		viaggiDaArchiviare.delete()

		logging.debug("Ora cancello tutti i record di LOG.")
		logDaEliminare.delete()

		startLog(Conducente)
		startLog(Viaggio)	# riabilita il log delle operazioni sul Viaggio

		request.user.message_set.create(message=u"Archiviazione effettuata.")
		vacuum_db()
		transaction.commit()
		return HttpResponseRedirect(reverse("tamArchiveUtil"))

	return render_to_response(template_name, 
							 {"archiveCount":archiveCount,
							  "logCount":logCount,
							  "archive_needed":archive_needed,
							  "end_date":end_date,
							  "end_date_string":end_date_string,
							},
							context_instance=RequestContext(request))


def view(request, template_name="archive/view.html"):
	""" Visualizza le corse archiviate """
	profile = ProfiloUtente.objects.get(user=request.user)
	from django.core.paginator import Paginator
	archiviati = ViaggioArchive.objects.filter(padre__isnull=True)
	paginator = Paginator(archiviati, 100, orphans=10)	# pagine da tot righe (cui si aggiungono i figli)

	try: page = int(request.GET.get("page"))
	except: page = 1
	paginator.smart_page_range = SmartPager(page, paginator.num_pages).results

	try:
		thisPage = paginator.page(page)
		list = thisPage.object_list
	except:
		request.user.message_set.create(message=u"Pagina %d vuota." % page)
		thisPage = None
		list = []

	luogoRiferimento = profile.luogo.nome

	return render_to_response(
		template_name,
		{'list':list, 'paginator':paginator, 'luogoRiferimento':luogoRiferimento, 'thisPage':thisPage },
		context_instance=RequestContext(request)
		)

def flat(request, template_name="archive/flat.html"):
	""" Livella le classifiche, in modo che gli ultimi abbiano zero """
	if not request.user.has_perm('tamArchive.flat'):
		request.user.message_set.create(message=u"Devi avere accesso all'appianamento.")
		return HttpResponseRedirect(reverse("tamArchiveUtil"))
	
	classificheViaggi = get_classifiche()

	def trovaMinimi(c1, c2):
		""" Date due classifiche (2 conducenti) ritorna il minimo """
		keys = ("puntiDiurni", "puntiNotturni",
				"prezzoDoppioPadova", "prezzoVenezia", "prezzoPadova")
		results = SortedDict()
		for key in keys:
			v1, v2 = c1[key], c2[key]
			if type(v1) is float: v1 = Decimal("%.2f" % v1)	# converto i float in Decimal
			if type(v2) is float: v2 = Decimal("%.2f" % v2)
			results[key] = min(v1, v2)
		return results

	minimi = reduce(trovaMinimi, classificheViaggi)
	flat_needed = (max(minimi.values()) > 0)	# controllo che ci sia qualche minimo da togliere
	if "flat" in request.POST and flat_needed:
		logAction("F",
					instance=request.user,
					description="Appianamento delle classifiche",
					user=request.user)
		logging.debug("FLAT delle classifiche")
		stopLog(Conducente)
		for conducente in Conducente.objects.all():
			conducente.classifica_iniziale_diurni -= minimi["puntiDiurni"]
			conducente.classifica_iniziale_notturni -= minimi["puntiNotturni"]
			conducente.classifica_iniziale_doppiPadova -= minimi['prezzoDoppioPadova']
			conducente.classifica_iniziale_long -= minimi['prezzoVenezia']
			conducente.classifica_iniziale_medium -= minimi['prezzoPadova']
			conducente.save()

		startLog(Conducente)
		request.user.message_set.create(message=u"Appianamento effettuato.")
		return HttpResponseRedirect(reverse("tamArchiveUtil"))

	return render_to_response(template_name, {"minimi":minimi, 'flat_needed':flat_needed},
							 context_instance=RequestContext(request))
