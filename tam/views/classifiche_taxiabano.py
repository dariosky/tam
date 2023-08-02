# coding: utf-8
from django.conf import settings

CLASSIFICHE = [
    {
        "nome": "Supplementari serali",
        "mapping_field": "puntiNotturni",
        "type": "supplementari",
        "image": "night",
        "viaggio_field": "punti_notturni",
    },
    {
        "nome": "Venezia-Treviso",
        "type": "punti",
        "mapping_field": "punti_abbinata",
        "viaggio_field": "punti_abbinata",
    },
    {
        "nome": "Lunghe",
        "prefix": "nelle",
        "descrizione": ">30km non abbinati",
        "mapping_field": "prezzoVenezia",
        "viaggio_field": "prezzoVenezia",
    },
    {
        "nome": "Doppi Padova",
        "prefix": "nelle",
        "mapping_field": "prezzoDoppioPadova",
        "viaggio_field": "prezzoDoppioPadova",
    },
    {
        "nome": "Corte",
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
    #    print "%d *****" % viaggio.id
    #
    #    for k in da:
    #        print "%15s: %s" % (k, da[k])

    if viaggio.padre_id is not None:
        return
    da = dettagliAbbinamento(viaggio, force_numDoppi=force_numDoppi)  # trovo i dettagli

    valoreTotale = viaggio.get_valuetot()
    #    print "Valore totale:", valoreTotale
    if da["VEorTV"]:
        # i VE/TV singoli con valore >=75€ vanno nelle lunghe
        if da["num_bacini"] == 1 and viaggio.lordo() > 90:
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
            if da["kmTotali"] <= settings.KM_PER_CORTE:
                viaggio.prezzoPadova = valoreTotale
            else:
                viaggio.prezzoVenezia = valoreTotale

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
    """Restituisce un dizionario con i dettagli dell'abbinamento
    la funzione viene usata solo nel caso la corsa sia un abbinamento (per il padre)
    Il rimanenteInLunghe va aggiunto alle Abbinate Padova se fa più di 1.25€/km alle Venezia altrimenti
    """
    kmTotali = viaggio.get_kmtot()
    # logging.debug("Km totali di %s: %s"%(viaggio.pk, kmTotali))

    baciniDiPartenza = []
    VEorTV = False

    def specialPlace(luogo):
        nome = luogo.nome.lower()
        return "venezia" in nome or "treviso" in nome

    total_pax = 0
    for cursore in [viaggio] + list(viaggio.viaggio_set.all()):
        if VEorTV is False and (specialPlace(cursore.da) or specialPlace(cursore.a)):
            VEorTV = True
        bacino = cursore.da
        if cursore.da.bacino:
            bacino = cursore.da.bacino  # prendo il luogo o il bacino
        if not bacino in baciniDiPartenza:
            baciniDiPartenza.append(bacino)
        total_pax += cursore.numero_passeggeri
    # logging.debug("Bacini di partenza: %d"%len(baciniDiPartenza))
    num_bacini = len(baciniDiPartenza)

    return {
        "kmTotali": kmTotali,
        "num_bacini": num_bacini,
        "VEorTV": VEorTV,
        "total_pax": total_pax,
    }


def get_value(viaggio, **kwargs):
    """Return the value of this trip on the scoreboard"""
    importoViaggio = viaggio.prezzo  # lordo
    forzaSingolo = False
    singolo = forzaSingolo or (not viaggio.is_abbinata)
    # logging.debug("Forzo la corsa come fosse un singolo:%s" % singolo)

    if viaggio.cartaDiCredito:
        importoViaggio *= Decimal(
            0.98
        )  # tolgo il 2% al lordo per i pagamenti con carta di credito

    if viaggio.commissione:  # tolgo la commissione dal lordo
        if viaggio.tipo_commissione == "P":
            importoViaggio = importoViaggio * (
                Decimal(1) - viaggio.commissione / Decimal(100)
            )  # commissione in percentuale
        else:
            importoViaggio = importoViaggio - viaggio.commissione

    importoViaggio = importoViaggio - viaggio.costo_autostrada

    #   Taxiabano non hanno abbuono per pagamento differito o fatturato
    if (
        viaggio.pagamento_differito or viaggio.fatturazione
    ) and settings.SCONTO_FATTURATE:
        # tolgo gli abbuoni (per differito o altro)
        importoViaggio = (
            importoViaggio * (100 - settings.SCONTO_FATTURATE) / Decimal(100)
        )

    ABBUONO_SOLO_SE_IMPORTO = getattr(settings, "ABBUONO_SOLO_SE_IMPORTO", False)
    if (
        ABBUONO_SOLO_SE_IMPORTO and importoViaggio > 0
    ):  # non do l'abbuono se non ho importo
        if viaggio.abbuono_fisso:
            importoViaggio -= viaggio.abbuono_fisso
        if viaggio.abbuono_percentuale:
            importoViaggio = importoViaggio * (
                Decimal(1) - viaggio.abbuono_percentuale / Decimal(100)
            )  # abbuono in percentuale

    importoViaggio = importoViaggio - viaggio.costo_sosta

    if settings.SCONTO_SOSTA:
        # aggiungo il prezzo della sosta scontato del SCONTO_SOSTA%
        importoViaggio += viaggio.prezzo_sosta * (
            Decimal(1) - settings.SCONTO_SOSTA / Decimal(100)
        )
    else:
        importoViaggio += viaggio.prezzo_sosta  # prezzo sosta intero
    return importoViaggio.quantize(Decimal(".01"))


GET_VALUE_FUNCTION = get_value
PROCESS_CLASSIFICHE_FUNCTION = process_classifiche
KM_PUNTO_ABBINATE = kmPuntoAbbinate
