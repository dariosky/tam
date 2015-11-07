# coding: utf-8
from pytz import timezone
from modellog.actions import logAction, stopLog, startLog
from django.contrib.auth.models import User
import logging
from django.db import transaction
from modellog.models import ActionLog
from django.db.models.query_utils import Q
from tam.tasks import print_timing, single_instance_task
from django.template.loader import render_to_string
import datetime
from tam.models import Viaggio, Conducente
from tamArchive.models import ViaggioArchive

logger = logging.getLogger('tam.archive')


# ===============================================================================

def vacuum_db(using='default'):
    from django.db import connections

    cursor = connections[using].cursor()
    logger.debug("Vacuum [%s]" % using)
    cursor.execute("VACUUM")


def archiveFromViaggio(viaggio):
    """ Crea una voce di archivio dato un viaggio
    @rtype : ViaggioArchive
    """
    # try:
    # path = viaggio.get_html_tragitto()
    # except:
    # path = "invalid path"
    # 	print path


    voceArchivio = ViaggioArchive(
        data=viaggio.data,
        da=viaggio.da,
        a=viaggio.a,
        path=viaggio.html_tragitto,
        pax=viaggio.numero_passeggeri,
        flag_esclusivo=viaggio.esclusivo,
        conducente=u"%s" % viaggio.conducente,
        flag_richiesto=viaggio.conducente_richiesto,
        cliente=(viaggio.cliente and viaggio.cliente.nome) or (
            viaggio.passeggero and viaggio.passeggero.nome),
        prezzo=viaggio.prezzo,
        prezzo_detail=render_to_string('corse/corse_prezzo_viaggio.inc.html',
                                       {"viaggio": viaggio, "nolink": True}),
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
    if not viaggio.annullato:
        if not viaggio.conducente:
            logger.warning("Il viaggio %d non ha un conducente." % viaggio.id)
            return ricordi
        conducente_id = viaggio.conducente.id
        ricordiConducente = ricordi.get(conducente_id, {})
        campiMemoria = ('punti_diurni', 'punti_notturni',
                        'prezzoVenezia', 'prezzoPadova', 'prezzoDoppioPadova',
                        'punti_abbinata')
        for nome_campo in campiMemoria:
            esistente = ricordiConducente.get(nome_campo, 0)
            ricordiConducente[nome_campo] = esistente + getattr(viaggio, nome_campo)
        ricordi[conducente_id] = ricordiConducente
    return ricordi


# ===============================================================================

def do_archiviazioneTask(user, end_date):
    """ Crea il task per l'archiviazione e lo schedula """
    from tam.models import TaskArchive

    archiviazione_task = TaskArchive(user=user, end_date=end_date)
    archiviazione_task.save()

    # ...and finally defer the task
    # task = djangotasks.task_for_object(archiviazione_task.do)
    # djangotasks.run_task(task)


def applyRicordi(ricordi):
    """ Cambia le statistiche dei conducenti per riflettere i viaggi archiviati """
    for conducente_id, classifica in ricordi.items():
        conducente = Conducente.objects.get(pk=conducente_id)
        conducente.classifica_iniziale_diurni += classifica['punti_diurni']
        conducente.classifica_iniziale_notturni += classifica['punti_notturni']

        conducente.classifica_iniziale_long += classifica['prezzoVenezia']
        conducente.classifica_iniziale_medium += classifica['prezzoPadova']
        conducente.classifica_iniziale_doppiPadova += classifica['prezzoDoppioPadova']
        conducente.classifica_iniziale_puntiDoppiVenezia += classifica['punti_abbinata']
        conducente.save()
    ricordi.clear()


# @task(name="archive.job")
@single_instance_task(60 * 30)  # 5 minutes timeout
@print_timing
# @transaction.commit_manually
# @transaction.commit_manually(using="archive")
# @transaction.commit_manually(using="modellog")
def do_archiviazione(user, end_date):
    # if settings.DEBUG:
    # raise Exception("Per archiviare devi uscire dal DEBUG mode.")

    filtroViaggi = Q(data__lt=end_date, padre__isnull=True)
    to_archive = Viaggio.objects.select_related("da", "a", "cliente", "conducente",
                                                "passeggero").filter(filtroViaggi)
    # Optimizations: mi faccio dare solo i modelli che mi interessano
    # Rimovo l'ordinamento di default
    logAction("K",
              instance=user,
              description="Archiviazione fino al %s" % end_date,
              user=user)
    logger.debug("Archiviazione fino al %s cominciata" % end_date)

    # disabilita il log delle operazioni: cancello viaggi e cambio conducenti
    stopLog(Viaggio)
    stopLog(Conducente)
    ricordi = {}  # ricordi[conducente_id] = {chiaveClassifica=valore}
    archiviati = 0
    chunkSize = 500
    total = to_archive.count()

    logger.debug(u"Archivio %d viaggi padre." % total)
    # to_archive = to_archive[:1]  # TODO: temp debug 1 viaggio
    while to_archive:
        # split viaggi padre in chucks
        viaggi_chunk, to_archive = to_archive[:chunkSize], to_archive[chunkSize:]
        with transaction.atomic():
            with transaction.atomic(using='archive'):
                for viaggiopadre in viaggi_chunk:
                    archivio_viaggiopadre = archiveFromViaggio(viaggiopadre)
                    daRicordareDelViaggio(ricordi, viaggiopadre)
                    archivio_viaggiopadre.save()
                    archiviati += 1

                    for figlio in viaggiopadre.viaggio_set.select_related("da", "a", "cliente",
                                                                          "conducente",
                                                                          "passeggero").order_by().all():
                        archivio_viaggiofiglio = archiveFromViaggio(figlio)
                        archivio_viaggiofiglio.padre = archivio_viaggiopadre
                        daRicordareDelViaggio(ricordi, figlio)
                        archivio_viaggiofiglio.save()
                    # archiviati += 1
                    viaggiopadre.delete()

                logger.debug("Modifico le classifiche e commit %d/%d" % (archiviati, total))
                applyRicordi(ricordi)

    logger.debug("fine archiviazione")
    if archiviati:
        vacuum_db()

    logDaEliminare = ActionLog.objects.filter(data__lt=end_date)
    contaLog = logDaEliminare.count()
    if contaLog:
        logger.debug("Ora cancello tutti i vecchi LOG.")
        logDaEliminare.delete()
        vacuum_db(using='modellog')

    # riabilita il log delle operazioni
    startLog(Conducente)
    startLog(Viaggio)

    logger.debug("Archiviazione fino al %s completata." % end_date.strftime("%d/%m/%Y"))


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    do_archiviazione(User.objects.get(id=1),
                     timezone('Europe/Rome').localize(datetime.datetime(2014, 2, 1)))
