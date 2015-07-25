# coding: utf-8
from django.conf import settings

CLASSIFICHE = [
    {"nome": "Supplementari serali",
     "mapping_field": "puntiNotturni",
     'type': 'supplementari',
     'image': "night",
     'viaggio_field': 'punti_notturni',
     },
    {"nome": "Venezia-Treviso",
     'type': 'punti',
     "mapping_field": "punti_abbinata",
     'viaggio_field': 'punti_abbinata',
     },
    {"nome": "Lunghe",
     "prefix": "nelle",
     "descrizione": ">30km non abbinati",
     "mapping_field": "prezzoVenezia",
     'viaggio_field': 'prezzoVenezia',
     },

    {"nome": "Doppi Padova",
     "prefix": "nelle",
     "mapping_field": "prezzoDoppioPadova",
     'viaggio_field': 'prezzoDoppioPadova',
     },
    {"nome": "Corte",
     "prefix": "nelle",
     "descrizione": "Padova, <=30km",
     "mapping_field": "prezzoPadova",
     "viaggio_field": "prezzoPadova",
     },
]

NOMI_CAMPI_CONDUCENTE = {
    "classifica_iniziale_diurni": "Supplementari diurni",
    "classifica_iniziale_notturni": "Supplementari notturni",
    "classifica_iniziale_puntiDoppiVenezia": "Punti VE-TV",
    "classifica_iniziale_prezzoDoppiVenezia": "Valore punti VE-TV",
    "classifica_iniziale_doppiPadova": "Valore Doppi Padova",
    "classifica_iniziale_long": "Valore Lunghe",
    "classifica_iniziale_medium": "Valore Corte (Padova)",
}

from decimal import Decimal

kmPuntoAbbinate = Decimal(120)


def process_classifiche(viaggio, force_numDoppi=None):
    #	print "%d *****" % viaggio.id
    #
    #	for k in da:
    #		print "%15s: %s" % (k, da[k])

    if viaggio.padre_id is not None:
        return
    if viaggio.id is None: return
    da = dettagliAbbinamento(viaggio, force_numDoppi=force_numDoppi)  # trovo i dettagli

    valoreTotale = viaggio.get_valuetot()
    #	print "Valore totale:", valoreTotale
    if da["VEorTV"]:
        # i VE/TV singoli con valore >=75€ vanno nelle lunghe
        if da["num_bacini"] == 1 and viaggio.lordo() >= 75:
            viaggio.prezzoVenezia = valoreTotale
        else:
            if viaggio.km_conguagliati:
                viaggio.punti_abbinata = 0  # corsa già conguagliata, zero punti
            else:
                viaggio.punti_abbinata = 1
            if viaggio.prezzo_sosta:
                # se ho un prezzo sosta nei Venezia-Treviso lo conto nelle lunghe
                viaggio.prezzoPunti = valoreTotale - viaggio.prezzo_sosta
                viaggio.prezzoVenezia = viaggio.prezzo_sosta
            else:
                viaggio.prezzoPunti = valoreTotale
    else:
        if da["num_bacini"] > 1:
            viaggio.prezzoDoppioPadova = valoreTotale  # corsa abbinata
        else:
            if da["kmTotali"] <= 30:
                viaggio.prezzoPadova = valoreTotale
            else:
                viaggio.prezzoVenezia = valoreTotale

            #		if da["puntiAbbinamento"] > 0:
            #			viaggio.punti_abbinata = da["puntiAbbinamento"]
            #			viaggio.prezzoPunti = da["valorePunti"]
            #			viaggio.prezzoVenezia = da["rimanenteInLunghe"]
            #		else:	# le corse abbinate senza punti si comportano come le singole
            #			if da["pricy"]:
            #				viaggio.prezzoDoppioPadova = da["rimanenteInLunghe"]
            #			else:
            #				prezzoNetto = da["rimanenteInLunghe"]
            #				if da["kmTotali"] >= 50:
            #					viaggio.prezzoVenezia = prezzoNetto
            #				elif 25 <= da["kmTotali"] < 50:
            #					viaggio.prezzoPadova = prezzoNetto
            #	elif viaggio.padre is None:	# corse non abbinate, o abbinate che non fanno alcun punto
            #		if viaggio.is_long():
            #			viaggio.prezzoVenezia = viaggio.prezzo_finale
            #
            #		# i figli non prendono nulla

    if viaggio.padre is None and valoreTotale > 0:
        # padri e singoli possono avere i supplementi
        # 27/1/2014 le corse al di sotto dei 27euro non generano supplementari. 13/3/2014 Abbasso i 27 a 0 euro
        # i 27 dovevano essere solo per il cliente fittizio
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
    kmTotali = viaggio.get_kmtot()
    valoreTotale = viaggio.get_valuetot()

    # logging.debug("Km totali di %s: %s"%(viaggio.pk, kmTotali))
    # logging.debug("kmNonConguagliati %s"%kmNonConguagliati)
    # kmNonConguagliati= kmTotali - viaggio.km_conguagliati
    # valoreDaConguagliare = viaggio.get_valuetot(forzaSingolo=forzaSingolo) * (kmNonConguagliati) / kmTotali
    # logging.debug("Valore da conguagliare %s"% valoreDaConguagliare)

    baciniDiPartenza = []
    VEorTV = False

    def specialPlace(luogo):
        nome = luogo.nome.lower()
        return ("venezia" in nome or "treviso" in nome)

    total_pax = 0
    for cursore in [viaggio] + list(viaggio.viaggio_set.all()):
        if VEorTV is False and (specialPlace(cursore.da) or specialPlace(cursore.a)):
            VEorTV = True
        bacino = cursore.da
        if cursore.da.bacino: bacino = cursore.da.bacino  # prendo il luogo o il bacino
        if not bacino in baciniDiPartenza:
            baciniDiPartenza.append(bacino)
        total_pax += cursore.numero_passeggeri
    # logging.debug("Bacini di partenza: %d"%len(baciniDiPartenza))
    num_bacini = len(baciniDiPartenza)
    #	if len(baciniDiPartenza) > 1:	# se partono tutti dalla stessa zona, non la considero un'abbinata
    #		partiAbbinamento = kmTotali / kmPuntoAbbinate	# è un Decimal
    #		puntiAbbinamento = int(partiAbbinamento)
    #		#logging.debug("Casette abbinamento %d, sarebbero %s" % (puntiAbbinamento, partiAbbinamento))
    #
    #	if (force_numDoppi is not None) and (force_numDoppi != puntiAbbinamento):
    #		#logging.debug("Forzo il numero di doppi a %d." % force_numDoppi)
    #		puntiAbbinamento = min(force_numDoppi, puntiAbbinamento) # forzo di punti doppio, max quello calcolato
    #
    #	kmRimanenti = kmTotali - (puntiAbbinamento * kmPuntoAbbinate)	# il resto della divisione per 120
    #
    #	if puntiAbbinamento:
    #		rimanenteInLunghe = kmRimanenti * Decimal("0.65")  # gli eccedenti li metto nei venezia a 0.65€/km
    #		#logging.debug("Dei %skm totali, %s sono fuori abbinta a 0.65 vengono %s "%(kmTotali, kmRimanenti, rimanenteInLunghe) )
    #		valorePunti = (valoreTotale - rimanenteInLunghe) / puntiAbbinamento
    #		#valorePunti = int(valoreDaConguagliare/partiAbbinamento)	# vecchio modo: valore punti in proporzioned
    #		valoreAbbinate = puntiAbbinamento * valorePunti
    #		pricy = False
    #	else:
    #		rimanenteInLunghe = Decimal(str(int(valoreTotale - valoreAbbinate))) # vecchio modo: il rimanente è il rimanente
    #		valorePunti = 0
    #
    #		if kmRimanenti:
    #			#lordoRimanente=viaggio.get_lordotot()* (kmNonConguagliati) / kmTotali
    #			lordoRimanente = viaggio.get_lordotot()
    #			#logging.debug("Mi rimangono euro %s in %s chilometri"%(lordoRimanente, kmTotali))
    #			euroAlKm = lordoRimanente / kmTotali
    #			#logging.debug("I rimanenti %.2fs km sono a %.2f euro/km" % (kmRimanenti, euroAlKm))
    #			pricy = euroAlKm > Decimal("1.25")
    #			#if pricy:
    #			#	logging.debug("Metto nei doppi Padova: %s" %rimanenteInLunghe)
    #			#else:
    #			#	logging.debug("Metto nei Venezia: %s" %rimanenteInLunghe)
    #
    #	if viaggio.km_conguagliati:
    #		# Ho già conguagliato dei KM, converto i KM in punti (il valore è definito sopra) quei punti li tolgo ai puntiAbbinamento
    #		#logging.debug("La corsa ha già %d km conguagliati, tolgo %d punti ai %d che avrebbe."  % (
    #		#				viaggio.km_conguagliati, viaggio.km_conguagliati/kmPuntoAbbinate, puntiAbbinamento) )
    #		puntiAbbinamento -= (viaggio.km_conguagliati / kmPuntoAbbinate)
    return {
        "kmTotali": kmTotali,
        "num_bacini": num_bacini,
        "VEorTV": VEorTV,
        "total_pax": total_pax,
    }


def get_value(viaggio, forzaSingolo=False):
    """ Return the value of this trip on the scoreboard """
    importoViaggio = viaggio.prezzo  # lordo
    forzaSingolo = False  # TMP
    singolo = forzaSingolo or (not viaggio.is_abbinata)
    if forzaSingolo:
        pass
    # logging.debug("Forzo la corsa come fosse un singolo:%s" % singolo)

    if viaggio.cartaDiCredito:
        importoViaggio *= Decimal(
            0.98)  # tolgo il 2% al lordo per i pagamenti con carta di credito

    if viaggio.commissione:  # tolgo la commissione dal lordo
        if viaggio.tipo_commissione == "P":
            importoViaggio = importoViaggio * (
                Decimal(1) - viaggio.commissione / Decimal(100))  # commissione in percentuale
        else:
            importoViaggio = importoViaggio - viaggio.commissione

    importoViaggio = importoViaggio - viaggio.costo_autostrada

    #   Taxiabano non hanno abbuono per pagamento differito o fatturato
    if (
                viaggio.pagamento_differito or viaggio.fatturazione) and settings.SCONTO_FATTURATE:  # tolgo gli abbuoni (per differito o altro)
        importoViaggio = importoViaggio * (100 - settings.SCONTO_FATTURATE) / Decimal(100)

    ABBUONO_SOLO_SE_IMPORTO = getattr(settings, 'ABBUONO_SOLO_SE_IMPORTO', False)
    if ABBUONO_SOLO_SE_IMPORTO and importoViaggio > 0:  # non do l'abbuono se non ho importo
        if viaggio.abbuono_fisso:
            importoViaggio -= viaggio.abbuono_fisso
        if viaggio.abbuono_percentuale:
            importoViaggio = importoViaggio * (
                Decimal(1) - viaggio.abbuono_percentuale / Decimal(100))  # abbuono in percentuale

    importoViaggio = importoViaggio - viaggio.costo_sosta

    if settings.SCONTO_SOSTA:
        importoViaggio += viaggio.prezzo_sosta * (
            Decimal(1) - settings.SCONTO_SOSTA / Decimal(
                100))  # aggiungo il prezzo della sosta scontato del 25%
    else:
        importoViaggio += viaggio.prezzo_sosta  # prezzo sosta intero
    return importoViaggio.quantize(Decimal('.01'))


GET_VALUE_FUNCTION = get_value
PROCESS_CLASSIFICHE_FUNCTION = process_classifiche
KM_PUNTO_ABBINATE = kmPuntoAbbinate

if __name__ == '__main__':
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    from tam.models import Viaggio

    viaggio = Viaggio.objects.get(id=13)
    print viaggio
    viaggio.km_conguagliati = 0
    viaggio.save()
    process_classifiche(viaggio)
    print "VETV punti:", viaggio.punti_abbinata, "valore:", viaggio.prezzoPunti, "conguagliato?", viaggio.km_conguagliati
    print "Doppi Padova:", viaggio.prezzoDoppioPadova
    print "Corte:", viaggio.prezzoPadova
    print "Lunghe", viaggio.prezzoVenezia
