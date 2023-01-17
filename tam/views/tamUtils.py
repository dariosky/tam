# coding: utf-8
from django.conf import settings


def getDefault(viaggio):
    """Restituisco un dizionario con tutti i valori di default del viaggio
    Di Viaggio usa:
        data	(per sapere se è notturno)
        da, a, luogo
        cliente (per listino e default)

    I default che vengono dal listino sono:
        prezzo, fatturazione, commissione e tipo_commissione

    @param viaggio: il viaggio di cui ottenere alcuni valori di default
    """
    default = {}
    cliente = viaggio.cliente

    if cliente:
        default["fatturazione"] = cliente.fatturazione
        default["incassato_albergo"] = cliente.incassato_albergo
        default["pagamento_differito"] = cliente.pagamento_differito
        if cliente.commissione > 0:
            default["tipo_commissione"] = cliente.tipo_commissione
        default["commissione"] = cliente.commissione

        if cliente.listino:
            prezzolistino = cliente.listino.get_prezzo(
                da=viaggio.da,
                a=viaggio.a,
                tipo_servizio=viaggio.esclusivo and "T" or "C",
                pax=viaggio.numero_passeggeri,
            )
            if prezzolistino:
                prezzoDaListinoNotturno = viaggio.trattaInNotturna()
                if prezzoDaListinoNotturno:
                    default["prezzo"] = prezzolistino.prezzo_notturno
                else:
                    default["prezzo"] = prezzolistino.prezzo_diurno
                # Fatturazione forzata dal listino
                if prezzolistino.flag_fatturazione == "S":
                    default["fatturazione"] = True
                elif prezzolistino.flag_fatturazione == "N":
                    default["fatturazione"] = False
                # Commissione forzata da listino
                if prezzolistino.commissione is not None:
                    default["commissione"] = prezzolistino.commissione
                    default["tipo_commissione"] = prezzolistino.tipo_commissione

    default["costo_autostrada"] = viaggio.costo_autostrada_default()

    # creando un viaggio di arrivo da una stazione/aeroporto
    if viaggio.da != viaggio.luogoDiRiferimento and viaggio.da.speciale != "-":
        if viaggio.da.speciale == "A":
            default["abbuono_fisso"] = settings.ABBUONO_AEROPORTI
        elif viaggio.da.speciale == "S":
            default["abbuono_fisso"] = settings.ABBUONO_STAZIONI

    return default


def conta_bacini_partenza(viaggi):
    bacini_di_partenza = set()
    for cursore in viaggi:
        bacino = cursore.da
        if cursore.da.bacino:
            bacino = cursore.da.bacino
        if bacino not in bacini_di_partenza:
            bacini_di_partenza.add(bacino)
            # logging.debug("Bacini di partenza: %d"%len(baciniDiPartenza))
    return bacini_di_partenza
