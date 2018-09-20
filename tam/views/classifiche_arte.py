# coding: utf-8
""" Definizione delle CLASSIFICHE
È una lista ordinata di dizionari
nome
descrizione (facoltativa)
mapping field (per indicare da che campo (dei viaggi) viene popolata la classifica
function (si usa per popolare i valori nel record del viaggio in modifica)
type (predefinito è 'prezzo', potrebbe essere anche 'punti' o 'supplementari')

verranno aggiungi in visualizzazione:
             'dati': con una lista ordinata per mapping_field di (chiave, conducente.nick, classifica)
               dove classifica tiene tutti i dati classifica del conducente (presi da SQL),
                un campo 'conducente'
                se è una classifica a punti tiene anche altri 3 campi:
                    abbinate: con tutti i viaggi del conducente ancora non completamente conguagliati
                    celle abbinate: una lista di punti del tipo {valore: x, data: x}
             'min', 'max': con i valori chiave massimi e minimi

"""
import datetime
from decimal import Decimal

import pytz
from django.utils.safestring import mark_safe

tz_italy = pytz.timezone('Europe/Rome')
DATA_CALCOLO_DOPPIINPARTENZA_COME_SINGOLI = tz_italy.localize(datetime.datetime(2016, 4, 1, 0, 0))

CLASSIFICHE = [
    {"nome": "Supplementari mattutini",
     "mapping_field": "puntiDiurni",
     'type': 'supplementari',
     'image': "morning",
     'viaggio_field': 'punti_diurni',
     },
    {"nome": "Supplementari serali",
     "mapping_field": "puntiNotturni",
     'type': 'supplementari',
     'image': "night",
     'viaggio_field': 'punti_notturni',
     },
    {"nome": "Venezia",
     "descrizione": ">=60km",
     "mapping_field": "prezzoVenezia",
     'viaggio_field': 'prezzoVenezia',
     'ignore_if_field': 'punti_abbinata',
     # ignoro questa classifica se ho dei punti abbinata
     },
    {"nome": "Doppi Venezia",
     'type': 'punti',
     "mapping_field": "punti_abbinata",
     "viaggio_field": "punti_abbinata",
     },
    {"nome": "Doppi Padova",
     "mapping_field": "prezzoDoppioPadova",
     'viaggio_field': 'prezzoDoppioPadova',
     },
    {"nome": "Padova",
     "descrizione": ">16€, <60km",
     "mapping_field": "prezzoPadova",
     'viaggio_field': 'prezzoPadova',
     },
]
NOMI_CAMPI_CONDUCENTE = {}  # tutto dai modelli

kmPuntoAbbinate = Decimal(120)


def process_classifiche(viaggio, force_numDoppi=None):
    KM_PER_LUNGHE = getattr(settings, 'KM_PER_LUNGHE', 50)
    if viaggio.is_abbinata and viaggio.padre is None:
        da = dettagliAbbinamento(viaggio, force_numDoppi=force_numDoppi)  # trovo i dettagli

        if viaggio.is_abbinata == 'P' and da['scoreVersion'] and da['scoreVersion'] >= '2016-04-01':
            # le abbinate in partenza si comportano come delle corse normali (ma usando i valori globali del gruppo)
            prezzoNetto = da["valoreTotale"]
            if da["kmTotali"] >= KM_PER_LUNGHE:
                viaggio.prezzoVenezia = prezzoNetto
            elif 25 <= da["kmTotali"] < KM_PER_LUNGHE:
                viaggio.prezzoPadova = prezzoNetto
        else:
            # per i padri abbinati, ma vere e proprie abbinate, non collettivi in partenza
            # print("Sono il padre di un abbinata da %s chilometri. Pricy: %s.\n%s"%(da["kmTotali"], da["pricy"], da) )
            if da["puntiAbbinamento"] > 0:
                viaggio.punti_abbinata = da["puntiAbbinamento"]
                viaggio.prezzoPunti = da["valorePunti"]
                viaggio.prezzoVenezia = da["rimanenteInLunghe"]
            else:  # le corse abbinate senza punti si comportano come le singole
                if da["pricy"]:
                    viaggio.prezzoDoppioPadova = da["rimanenteInLunghe"]
                else:
                    prezzoNetto = da["rimanenteInLunghe"]
                    if da["kmTotali"] >= KM_PER_LUNGHE:
                        viaggio.prezzoVenezia = prezzoNetto
                    elif 25 <= da["kmTotali"] < KM_PER_LUNGHE:
                        viaggio.prezzoPadova = prezzoNetto
    elif viaggio.padre_id is None:  # corse non abbinate, o abbinate che non fanno alcun punto
        if viaggio.is_long():
            viaggio.prezzoVenezia = viaggio.prezzo_finale
        elif viaggio.is_medium():
            viaggio.prezzoPadova = viaggio.prezzo_finale
            # i figli non prendono nulla

    if viaggio.padre_id is None:  # padri e singoli possono avere i supplementi
        for fascia, points in viaggio.disturbi().items():
            if fascia == "night":
                viaggio.punti_notturni += points
            else:
                viaggio.punti_diurni += points


def dettagliAbbinamento(viaggio, force_numDoppi=None):
    """ Restituisce un dizionario con i dettagli dell'abbinamento
        la funzione viene usata solo nel caso la corsa sia un abbinamento (per il padre)
        Il rimanenteInLunghe va aggiunto alle Abbinate Padova se fa più di 1.25€/km alle Venezia altrimenti
    """
    from tam.views.tamUtils import conta_bacini_partenza

    kmNonConguagliati = 0
    partiAbbinamento = 0
    valoreDaConguagliare = 0
    valorePunti = 0
    puntiAbbinamento = 0
    valoreAbbinate = 0
    rimanenteInLunghe = 0
    kmRimanenti = 0
    pricy = False

    kmTotali = viaggio.get_kmtot()
    # logging.debug("Km totali di %s: %s"%(viaggio.pk, kmTotali))

    if kmTotali == 0:
        return locals()

    # logging.debug("kmNonConguagliati %s"%kmNonConguagliati)
    forzaSingolo = (force_numDoppi is 0)
    baciniDiPartenza = conta_bacini_partenza([viaggio] + list(viaggio.viaggio_set.all()))

    scoreVersion = None  # We keep a progressive date 'yyyy-mm-dd-vv' to track version changes
    if viaggio.data >= DATA_CALCOLO_DOPPIINPARTENZA_COME_SINGOLI and len(baciniDiPartenza) == 1:
        scoreVersion = '2016-04-01'

    valoreTotale = viaggio.get_valuetot(forzaSingolo=forzaSingolo, scoreVersion=scoreVersion)

    # kmNonConguagliati= kmTotali - viaggio.km_conguagliati
    # valoreDaConguagliare = viaggio.get_valuetot(forzaSingolo=forzaSingolo) * (kmNonConguagliati) / kmTotali
    # logging.debug("Valore da conguagliare %s"% valoreDaConguagliare)

    # se partono tutti dalla stessa zona, non la considero un'abbinata
    if len(baciniDiPartenza) > 1:
        partiAbbinamento = kmTotali / kmPuntoAbbinate  # è un Decimal
        puntiAbbinamento = int(partiAbbinamento)
    # logging.debug("Casette abbinamento %d, sarebbero %s" % (puntiAbbinamento, partiAbbinamento))

    if (force_numDoppi is not None) and (force_numDoppi != puntiAbbinamento):
        # logging.debug("Forzo il numero di doppi a %d." % force_numDoppi)
        # forzo di punti doppio, max quello calcolato
        puntiAbbinamento = min(force_numDoppi, puntiAbbinamento)

    # il resto della divisione per 120
    kmRimanenti = kmTotali - (puntiAbbinamento * kmPuntoAbbinate)

    if puntiAbbinamento:
        rimanenteInLunghe = kmRimanenti * Decimal(
            "0.65")  # gli eccedenti li metto nei venezia a 0.65€/km
        # logging.debug("Dei %skm totali: %s fuori abbinta a 0.65 a %s "%(kmTotali, kmRimanenti, rimanenteInLunghe) )
        valorePunti = (valoreTotale - rimanenteInLunghe) / puntiAbbinamento
        # valorePunti = int(valoreDaConguagliare/partiAbbinamento)	# vecchio modo: valore punti in proporzioned
        valoreAbbinate = puntiAbbinamento * valorePunti
        pricy = False
    else:
        # vecchio modo: il rimanente è il rimanente
        rimanenteInLunghe = Decimal(str(int(valoreTotale - valoreAbbinate)))
        valorePunti = 0

        if kmRimanenti:
            # lordoRimanente=viaggio.get_lordotot()* (kmNonConguagliati) / kmTotali
            lordoRimanente = viaggio.get_lordotot()
            # logging.error("Mi rimangono euro %s in %s chilometri"%(lordoRimanente, kmTotali))
            euroAlKm = lordoRimanente / kmTotali
            # logging.error("I rimanenti %.2fs km sono a %.2f euro/km" % (kmRimanenti, euroAlKm))
            pricy = euroAlKm > Decimal("1.25")
            # if pricy:
            #   logging.debug("Metto nei doppi Padova: %s" %rimanenteInLunghe)
            # else:
            #   logging.debug("Metto nei Venezia: %s" %rimanenteInLunghe)

    if viaggio.km_conguagliati:
        # Ho già conguagliato dei KM, converto i KM in punti (il valore è definito sopra)
        #  quei punti li tolgo ai puntiAbbinamento
        # logging.debug("La corsa ha già %d km conguagliati, tolgo %d punti ai %d che avrebbe."  % (
        #               viaggio.km_conguagliati, viaggio.km_conguagliati/kmPuntoAbbinate, puntiAbbinamento) )
        puntiAbbinamento -= (viaggio.km_conguagliati / kmPuntoAbbinate)
    return dict(kmTotali=kmTotali,
                puntiAbbinamento=puntiAbbinamento,
                valorePunti=valorePunti,
                rimanenteInLunghe=rimanenteInLunghe,
                pricy=pricy,
                valoreTotale=valoreTotale,
                scoreVersion=scoreVersion,
                )


def get_value(viaggio, forzaSingolo=False, scoreVersion=None):
    """ Return the value of this trip on the scoreboard """
    singolo = forzaSingolo or (not viaggio.is_abbinata)
    # logging.debug("Forzo la corsa come fosse un singolo:%s" % singolo)
    if viaggio.is_abbinata and viaggio.padre is not None:
        padre = viaggio.padre
        if padre.is_abbinata == "P" and scoreVersion and scoreVersion >= '2016-04-01':
            # i figli degli abbinati in partenza sono nulli
            return 0

    # logging.info("Using scoreVersion: %s" % scoreVersion)
    if viaggio.is_abbinata == "P" and scoreVersion and scoreVersion >= '2016-04-01':
        viaggi = [viaggio] + list(viaggio.viaggio_set.all())
        importiViaggio = []  # tengo gli importi viaggi distinti (per poter poi calcolarne le commissioni individuali)
        multiplier = 1
        for i, v in enumerate(viaggi):
            importo_riga = v.prezzo
            if viaggio.cartaDiCredito:
                importo_riga *= Decimal(0.98)  # tolgo il 2% al lordo per i pagamenti con carta di credito
            if v.commissione:  # tolgo la commissione dal lordo
                if v.tipo_commissione == "P":
                    # commissione in percentuale
                    importo_riga *= (Decimal(1) - v.commissione / Decimal(100))
                else:
                    importo_riga = importo_riga - v.commissione

            importo_riga = importo_riga - v.costo_autostrada
            importiViaggio.append(importo_riga)

        km = viaggio.get_kmtot()
        if km:
            renditaChilometrica = sum(importiViaggio) / km
        else:
            renditaChilometrica = 0

        if km >= getattr(settings, 'KM_PER_LUNGHE', 50):
            if renditaChilometrica < Decimal("0.65"):
                multiplier = renditaChilometrica / Decimal("0.65")
                # logging.debug("Sconto Venezia sotto rendita: %s" % renditaChilometrica)
        elif 25 <= km < getattr(settings, 'KM_PER_LUNGHE', 50) or (
            km < 25 and sum(importiViaggio) > 16):
            if renditaChilometrica < Decimal("0.8"):
                multiplier = renditaChilometrica / Decimal("0.8")
                # logging.debug("Sconto Padova sotto rendita: %s" % renditaChilometrica)

        for i, v in enumerate(viaggi):
            importoViaggio = importiViaggio[i]
            if (v.pagamento_differito or v.fatturazione) and settings.SCONTO_FATTURATE:
                # tolgo gli abbuoni (per differito o altro)
                importoViaggio = importoViaggio * (100 - settings.SCONTO_FATTURATE) / Decimal(100)
            if v.abbuono_fisso:
                importoViaggio -= v.abbuono_fisso
            if v.abbuono_percentuale:
                # abbuono in percentuale
                importoViaggio = importoViaggio * (
                    Decimal(1) - v.abbuono_percentuale / Decimal(100))

            importoViaggio = importoViaggio - v.costo_sosta

            if settings.SCONTO_SOSTA:
                # aggiungo il prezzo della sosta scontato del 25%
                importoViaggio += v.prezzo_sosta * (
                    Decimal(1) - settings.SCONTO_SOSTA / Decimal(100))
            else:
                importoViaggio += v.prezzo_sosta  # prezzo sosta intero
            importiViaggio[i] = importoViaggio

        importoViaggio = sum(importiViaggio) * multiplier

    else:
        # Viaggi singoli
        importoViaggio = viaggio.prezzo  # lordo
        if viaggio.cartaDiCredito:
            importoViaggio *= Decimal(0.98)  # tolgo il 2% al lordo per i pagamenti con carta di credito
        if viaggio.commissione:  # tolgo la commissione dal lordo
            if viaggio.tipo_commissione == "P":
                # commissione in percentuale
                importoViaggio = importoViaggio * (Decimal(1) - viaggio.commissione / Decimal(100))
            else:
                importoViaggio = importoViaggio - viaggio.commissione

        importoViaggio = Decimal(importoViaggio - viaggio.costo_autostrada)

        km = viaggio.get_kmtot()
        # per le corse singole
        if singolo:
            chilometriTotali = km
            if chilometriTotali:
                renditaChilometrica = importoViaggio / chilometriTotali
            else:
                renditaChilometrica = 0
            if viaggio.is_long():
                if renditaChilometrica < Decimal("0.65"):
                    importoViaggio *= renditaChilometrica / Decimal("0.65")
                    # logging.debug("Sconto Venezia sotto rendita: %s" % renditaChilometrica)
            elif viaggio.is_medium():
                if renditaChilometrica < Decimal("0.8"):
                    importoViaggio *= renditaChilometrica / Decimal("0.8")
                    # logging.debug("Sconto Padova sotto rendita: %s" % renditaChilometrica)

        if (viaggio.pagamento_differito or viaggio.fatturazione) and settings.SCONTO_FATTURATE:
            # tolgo gli abbuoni (per differito o altro)
            importoViaggio = importoViaggio * (100 - settings.SCONTO_FATTURATE) / Decimal(100)
        if viaggio.abbuono_fisso:
            importoViaggio -= viaggio.abbuono_fisso
        if viaggio.abbuono_percentuale:
            # abbuono in percentuale
            importoViaggio = importoViaggio * (
                Decimal(1) - viaggio.abbuono_percentuale / Decimal(100))
        importoViaggio = importoViaggio - viaggio.costo_sosta

        if settings.SCONTO_SOSTA:
            # aggiungo il prezzo della sosta scontato del 25%
            importoViaggio += viaggio.prezzo_sosta * (
                Decimal(1) - settings.SCONTO_SOSTA / Decimal(100))
        else:
            importoViaggio += viaggio.prezzo_sosta  # prezzo sosta intero

    return importoViaggio.quantize(Decimal('.01'))


GET_VALUE_FUNCTION = get_value
PROCESS_CLASSIFICHE_FUNCTION = process_classifiche
KM_PUNTO_ABBINATE = kmPuntoAbbinate


def gettoneDoppioSeFeriale(calendar):
    """
        Restituisce il valore a gettoni, doppio se il calendario è in un giorno festivo o prefestivo
    """
    reference_date = calendar.date_start.astimezone(tz_italy)
    if reference_date.weekday() in (5, 6):
        return 2
    md = reference_date.timetuple()[1:3]
    if md in (
        (1, 1),  # Capodanno
        (1, 6),  # Epifania
        (4, 25),  # 25 aprile
        (5, 1),  # primo maggio, festa del lavoro
        (6, 2),  # 2 giugno, festa della repubblica
        (8, 15),  # ferragosto
        (11, 1),  # ognissanti
        (12, 8),  # immacolata
        (12, 25),  # Natale
        (12, 26),  # S.Stefano
    ):
        return 2

    return 1


def cal_display_mattino_pomeriggio(calendar):
    reference_date = calendar.date_start.astimezone(tz_italy)
    result = u""
    if reference_date.hour <= 12:
        result += u"mattino"
    else:
        result += u"pomeriggio"
    if calendar.value > 1:
        result += u" x%d" % calendar.value
    return result


def cal_display_allday2_halfday1(calendar):
    reference_date = calendar.date_start.astimezone(tz_italy)
    result = u""
    if calendar.minutes < 60 * 24:
        if reference_date.hour <= 12:
            result += u"mattino"
        else:
            result += u"pomeriggio"
    else:
        result += u"tutto il giorno"
    return result


def value_allday2_halday1(calendar):  # gettone di valore sempre unitario
    if calendar.minutes > 60 * 14:
        value = 2
    else:
        value = 1
    return value


def cal_display_dimezzato(rank_total):
    """ Visualizza il totale in giorni di una classifica a gettoni, dove ogni gettone è mezza giornata """
    result_int = 0
    if rank_total % 2 == 0:
        result_int = rank_total / 2
        fract = ""
    else:
        result_int = int(rank_total / 2)
        fract = " &frac12;"

    suffix = 'giorno' if result_int <= 1 else 'giorni'
    if result_int == 0:
        result_int = ""
    return mark_safe(
        u"{giorni}{fract} {suffix}".format(giorni=result_int, fract=fract,
                                           suffix=suffix))


def toggle_1or2(calendar):
    calendar.value = 1 if calendar.value == 2 else 2  # toogle between 1 and 2
    calendar.save()


from django.conf import settings
