# coding: utf-8
from modellog.actions import logAction, stopLog, startLog
from django.contrib.auth.models import User
from tam.models import Viaggio, Conducente, reallySpaceless
import logging
from django.db import transaction
from modellog.models import ActionLog
from django.db.models.query_utils import Q
from tam.tasks import print_timing, single_instance_task
from celery.task import task
from tamArchive.models import ViaggioArchive
from django.template.loader import render_to_string
import datetime
from django.conf import settings
#===============================================================================

def vacuum_db(using='default'):
	print "VACUUM %s" % using
	from django.db import connections
	cursor = connections[using].cursor()
	logging.debug("Vacuum [%s]" % using)
	cursor.execute("VACUUM")
	transaction.set_dirty(using=using)


def archiveFromViaggio(viaggio):
	""" Crea una voce di archivio dato un viaggio """
	try:
		path = viaggio.get_html_tragitto()
	except:
		path = "invalid path"
		print path	
	voceArchivio = ViaggioArchive(
			data=viaggio.data,
			da=viaggio.da,
			a=viaggio.a,
			path=path,
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

#===============================================================================

@task(name="archive.job")
@single_instance_task(60 * 30)	# 5 minutes timeout
@print_timing
@transaction.commit_manually
@transaction.commit_manually(using="archive")
@transaction.commit_manually(using="modellog")
def do_archiviazione(user_id, end_date):
	if settings.DEBUG:
		print "L'archiviazione non è effettuabile finché sei in modalità DEBUG."
		return
	user = User.objects.get(id=user_id)
	filtroViaggi = Q(data__lt=end_date, conducente__isnull=False, padre__isnull=True)
	viaggiDaArchiviare = Viaggio.objects.select_related("da", "a", "cliente", "conducente", "passeggero").order_by().filter(filtroViaggi)
		# Optimizations: mi faccio dare solo i modelli che mi interessano
		# Rimovo l'ordinamento di default
	logAction("K",
				instance=user,
				description="Archiviazione fino al %s" % end_date,
				user=user)
	logging.debug("Archiviazione fino al %s cominciata" % end_date)

	# disabilita il log delle operazioni
	stopLog(Viaggio)
	stopLog(Conducente)
	ricordi = {}	# ricordi[conducente_id] = {chiaveClassifica=valore}
	archiviati = 0
	pendingChanges = 0
	chunkSize = 500

	def applyRicordi(ricordi):
		""" Cambia le statistiche dei conducenti per riflettere i viaggi archiviati """
		print "apply %d changes" % pendingChanges
		for conducente_id, classifica in ricordi.items():
			conducente = Conducente.objects.get(pk=conducente_id)
			conducente.classifica_iniziale_diurni += classifica['punti_diurni']
			conducente.classifica_iniziale_notturni += classifica['punti_notturni']

			conducente.classifica_iniziale_long += classifica['prezzoVenezia']
			conducente.classifica_iniziale_medium += classifica['prezzoPadova']
			conducente.classifica_iniziale_doppiPadova += classifica['prezzoDoppioPadova']
			conducente.classifica_iniziale_puntiDoppiVenezia += classifica['punti_abbinata']
			conducente.save()
		logging.debug("Effettuo il commit [%d]" % archiviati)
		transaction.commit(using='archive')
		transaction.commit()
		ricordi.clear()

	print "Archivio %d viaggi padre." % viaggiDaArchiviare.count()
	for viaggio in viaggiDaArchiviare:
		archiviati += 1
		pendingChanges += 1

		viaggioArchiviato = archiveFromViaggio(viaggio)
		daRicordareDelViaggio(ricordi, viaggio)
		viaggioArchiviato.save()

		for figlio in viaggio.viaggio_set.select_related("da", "a", "cliente", "conducente", "passeggero").order_by().all():
			viaggioArchiviatoFiglio = archiveFromViaggio(figlio)
			viaggioArchiviatoFiglio.padre = viaggioArchiviato
			daRicordareDelViaggio(ricordi, figlio)
			viaggioArchiviatoFiglio.save()
			archiviati += 1
			pendingChanges += 1
		viaggio.delete()

		if pendingChanges >= chunkSize:
			applyRicordi(ricordi)
			pendingChanges = 0
	print "fine"
	if pendingChanges:
		applyRicordi(ricordi)
	if archiviati:
		vacuum_db()
		transaction.commit()


	#logging.debug("Cancello tutti i viaggi appena archiviati")
	#viaggiDaArchiviare.delete()

	logDaEliminare = ActionLog.objects.filter(data__lt=end_date)
	contaLog = logDaEliminare.count()
	if contaLog:
		logging.debug("Ora cancello tutti i record di LOG.")
		logDaEliminare.delete()
		vacuum_db(using='modellog')
		transaction.commit(using='modellog')

	transaction.set_clean(using='modellog')
	transaction.set_clean()

	# riabilita il log delle operazioni
	startLog(Conducente)
	startLog(Viaggio)

	logging.debug("Archiviazione fino al %s completata." % end_date)


if __name__ == '__main__':
	do_archiviazione.run(1, datetime.date(2011, 1, 1))
