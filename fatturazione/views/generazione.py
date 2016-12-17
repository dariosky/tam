# encoding: utf-8
'''
Created on 11/set/2011

@author: Dario
'''
import datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponseRedirect

from fatturazione.models import Fattura, RigaFattura, nomi_fatture, \
    nomi_plurale
from fatturazione.views.util import ultimoProgressivoFattura
from modellog.actions import logAction
from tam.models import Viaggio, ProfiloUtente
from tam.tamdates import MONTH_NAMES
from . import tipi_fatturazione

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

from django.shortcuts import render
from tam.tamdates import parse_datestring
from django.conf import settings
import tam.tamdates as tamdates

PREZZO_VIAGGIO_NETTO = getattr(settings, 'PREZZO_VIAGGIO_NETTO', True)
NOMI_DEFINIZIONE_FATTURE = getattr(settings, 'NOMI_DEFINIZIONE_FATTURE')

DEFINIZIONE_FATTURE = []
for nome_classe in NOMI_DEFINIZIONE_FATTURE:
    DEFINIZIONE_FATTURE.append(getattr(tipi_fatturazione, nome_classe))

FATTURE_PER_TIPO = {}
for fatturazione in DEFINIZIONE_FATTURE:
    FATTURE_PER_TIPO[fatturazione.codice] = fatturazione


@permission_required('fatturazione.generate', '/')
def lista_fatture_generabili(request, template_name="1_scelta_fatture.html"):
    get_mese_fatture = request.GET.get('mese', None)
    oggi = tamdates.ita_today()
    quick_month_names = [MONTH_NAMES[(oggi.month - 3) % 12],
                         MONTH_NAMES[(oggi.month - 2) % 12],
                         MONTH_NAMES[(oggi.month - 1) % 12]]  # current month
    quick_month_names.reverse()
    if get_mese_fatture:
        if get_mese_fatture == "cur":
            data_start = oggi.replace(day=1)
            data_end = (data_start + datetime.timedelta(days=32)).replace(
                day=1) - datetime.timedelta(days=1)
        elif get_mese_fatture == 'prev':
            data_end = oggi.replace(day=1) - datetime.timedelta(days=1)  # vado a fine mese scorso
            data_start = data_end.replace(day=1)  # vado a inizio del mese precedente
        elif get_mese_fatture == 'prevprev':  # due mesi fa
            data_end = (oggi.replace(day=1) - datetime.timedelta(days=1)).replace(
                day=1) - datetime.timedelta(
                days=1)  # vado a inizio mese scorso
            data_start = data_end.replace(day=1)  # vado a inizio di due mesi fa
        else:
            raise Exception("Unexpected get mese fatture %s" % get_mese_fatture)
    else:
        data_start = parse_datestring(  # dal primo del mese scorso
            request.GET.get("data_start"),
            default=(tamdates.ita_today().replace(
                day=1) - datetime.timedelta(
                days=1)).replace(day=1)
        )
        data_end = parse_datestring(  # all'ultimo del mese scorso
            request.GET.get("data_end"),
            default=tamdates.ita_today().replace(
                day=1) - datetime.timedelta(days=1)
        )

    # prendo i viaggi da fatturare
    # dalla mezzanotte del primo giorno alla mezzanotte esclusa del giorno dopo l'ultimo
    gruppo_fatture = []

    for fatturazione in DEFINIZIONE_FATTURE:
        if not fatturazione.generabile: continue
        selezione = fatturazione.origine.objects
        selezione = selezione.filter(fatturazione.filtro)

        if fatturazione.origine == Viaggio:
            #			selezione = selezione.filter(id=81833)	#DEBUG:
            selezione = selezione.filter(data__gte=data_start,
                                         data__lt=data_end + datetime.timedelta(
                                             days=1))

            selezione = selezione.select_related("da", "a", "cliente",
                                                 "conducente", "passeggero",
                                                 "padre")
        if fatturazione.origine == RigaFattura:
            selezione = selezione.filter(viaggio__data__gte=data_start,
                                         viaggio__data__lte=data_end + datetime.timedelta(
                                             days=1))
            selezione = selezione.select_related("viaggio__da", "viaggio__a",
                                                 "viaggio__cliente",
                                                 "viaggio__conducente",
                                                 "viaggio__passeggero",
                                                 'fattura', 'conducente')
        selezione = selezione.order_by(*fatturazione.order_by)

        dictFatturazione = {"d": fatturazione,
                            # la definizione della fatturazione
                            "lista": selezione,
                            }
        if hasattr(fatturazione, "update_context"):
            dictFatturazione["parametri"] = fatturazione.update_context(
                data_start, data_end) if hasattr(fatturazione,
                                                 "update_context") else {}
        else:
            dictFatturazione["parametri"] = {}
        gruppo_fatture.append(dictFatturazione)
    oggi = tamdates.ita_today()

    profile = ProfiloUtente.objects.get(user=request.user)
    luogoRiferimento = profile.luogo
    return render(
        request,
        template_name,
        {
            "today": oggi,
            "luogoRiferimento": luogoRiferimento,
            "data_start": data_start,
            "data_end": data_end,
            "dontHilightFirst": True,
            "mediabundleJS": ('tamUI',),
            "mediabundleCSS": ('tamUI',),

            "gruppo_fatture": gruppo_fatture,
            'PREZZO_VIAGGIO_NETTO': PREZZO_VIAGGIO_NETTO,
            "quick_month_names": quick_month_names,
        },
    )


def on_fattura_end(fattura, esente_iva):
    # add the tax stamp if needed at the end of the invoice
    if esente_iva and fattura.val_totale() >= settings.MIN_PRICE_FOR_TAXSTAMP:
        # alle esenti IVA metto l'imposta di bollo
        aggregation = fattura.righe.aggregate(Max('riga'))
        num_riga = aggregation.get('riga__max', 0) + 10
        riga_fattura = RigaFattura(
            descrizione="Imposta di bollo", qta=1, iva=0,
            prezzo=Decimal("2.00"), riga=num_riga)
        riga_fattura.fattura = fattura
        riga_fattura.save()


@transaction.atomic
@permission_required('fatturazione.generate', '/')
# template_name, tipo, filtro, keys, order_by, manager
def genera_fatture(request, fatturazione):
    tipo = fatturazione.codice
    template_name = fatturazione.template_generazione
    manager = fatturazione.origine.objects
    order_by = fatturazione.order_by
    filtro = fatturazione.filtro
    keys = fatturazione.keys

    ids = request.POST.getlist("id")
    plurale = nomi_plurale[tipo]
    conducenti_ricevute = None
    anno = 0  # usato solo con le fatture consorzio

    if not ids:
        messages.error(request, "Devi selezionare qualche corsa da fatturare.")
        return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

    data_generazione = parse_datestring(request.POST['data_generazione'])
    if fatturazione.ask_progressivo:  # la generazione fatture consorzio richiede anno e progressivo - li controllo
        try:
            anno = int(request.POST.get("anno"))
        except:
            messages.error(request, "Seleziona un anno numerico.")
            return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
        try:
            progressivo = int(request.POST.get("progressivo", 1))
        except:
            messages.error(request,
                           "Ho bisogno di un progressivo iniziale numerico.")
            return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
        ultimo_progressivo = ultimoProgressivoFattura(anno, tipo)
        if ultimo_progressivo >= progressivo:
            messages.error(request,
                           "Il progressivo è troppo piccolo, ho già la %s %s/%s." % (
                               nomi_fatture[tipo], anno, ultimo_progressivo))
            return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
    else:
        progressivo = 0  # nelle ricevute lo uso per ciclare
    progressivo_iniziale = progressivo

    lista = manager.filter(id__in=ids)
    lista = lista.filter(filtro)
    if manager.model == Viaggio:
        lista = lista.select_related("da", "a", "cliente", "conducente",
                                     "passeggero", "padre")
    elif manager.model == RigaFattura:
        lista = lista.select_related("viaggio__da", "viaggio__a",
                                     "viaggio__cliente", "viaggio__conducente",
                                     "viaggio__passeggero",
                                     'fattura', 'conducente')
    if order_by is None:
        order_by = keys + ["data"]  # ordino per chiave - quindi per data
    lista = lista.order_by(*order_by).all()
    if not lista:
        messages.error(request,
                       "Tutte le %s selezionate sono già state fatturate." % plurale)
        return HttpResponseRedirect(reverse("tamGenerazioneFatture"))
    fatture = 0

    lastKey = None
    for elemento in lista:
        key = [getattr(elemento, keyName) for keyName in keys]
        if lastKey != key:
            if lastKey != None:
                progressivo += 1
            lastKey = key
            fatture += 1

        elemento.key = key
        if fatturazione.ask_progressivo:
            elemento.codice_fattura = fatturazione.codice_fattura
            elemento.progressivo_fattura = progressivo
            elemento.anno_fattura = anno

    if request.method == "POST":
        if "generate" in request.POST:
            lastKey = None
            fattura = None
            fatture_generate = 0

            for elemento in lista:
                if manager.model == RigaFattura:
                    viaggio = elemento.viaggio
                else:
                    viaggio = elemento

                if elemento.key != lastKey:
                    if fattura:
                        on_fattura_end(fattura, esente_iva)
                    # TESTATA
                    fattura = Fattura(tipo=tipo)
                    data_fattura = data_generazione
                    fattura.data = data_fattura
                    if fatturazione.ask_progressivo:
                        fattura.anno = anno
                        fattura.progressivo = viaggio.progressivo_fattura

                    if fatturazione.destinatario == "cliente":
                        # popolo il destinatario della fattura
                        if viaggio.cliente:
                            fattura.cliente = viaggio.cliente
                            fattura.emessa_a = viaggio.cliente.dati or viaggio.cliente.nome
                        elif viaggio.passeggero:
                            fattura.passeggero = viaggio.passeggero
                            fattura.emessa_a = viaggio.passeggero.dati or viaggio.passeggero.nome
                    elif fatturazione.destinatario == "consorzio":
                        fattura.emessa_a = settings.DATI_CONSORZIO
                    else:
                        raise Exception(
                            "%s non è un valido destinatario." % fatturazione.destinatario)

                    if getattr(fatturazione, 'note', ""):
                        fattura.note = fatturazione.note

                    if fatturazione.mittente == "consorzio":
                        fattura.emessa_da = settings.DATI_CONSORZIO
                    elif fatturazione.mittente == "conducente":
                        fattura.emessa_da = viaggio.conducente.dati or viaggio.conducente.nome
                    else:
                        raise Exception(
                            "%s non è un valido mittente." % fatturazione.mittente)
                    fattura.save()
                    fatture_generate += 1
                    riga = 10

                    if callable(fatturazione.esente_iva):
                        esente_iva = fatturazione.esente_iva(elemento)
                    else:
                        esente_iva = fatturazione.esente_iva

                    lastKey = elemento.key

                # RIGHE dettaglio
                riga_fattura = RigaFattura()
                riga_fattura.riga = riga  # progressivo riga
                riga_fattura.conducente = elemento.conducente

                if manager.model == RigaFattura:  # fattura da altra fattura
                    campi_da_riportare = "descrizione", "qta"
                    for campo in campi_da_riportare:
                        setattr(riga_fattura, campo, getattr(elemento, campo))

                    if not esente_iva and hasattr(fatturazione, 'iva_forzata'):
                        # le fatture senza IVA per i conducenti che non le emettono, hanno IVA comunque
                        riga_fattura.iva = fatturazione.iva_forzata
                    else:
                        # altrimenti riporto l'iva dalla fattura di origine
                        riga_fattura.iva = elemento.iva

                    if viaggio:
                        # us price of the run if we have it
                        riga_fattura.prezzo = viaggio.prezzo_netto(
                            riga_fattura.iva)
                        if viaggio.cliente:
                            riga_fattura.note = viaggio.cliente.nome
                        elif viaggio.passeggero:
                            riga_fattura.note = viaggio.passeggero.nome
                    else:
                        riga_fattura.prezzo = elemento.prezzo  # ... if or price of the item
                    riga_fattura.riga_fattura_consorzio = elemento

                else:  # fattura da un viaggio

                    riga_fattura.descrizione = "%s-%s %s %dpax %s" % \
                                               (viaggio.da, viaggio.a,
                                                viaggio.data.astimezone(
                                                    tamdates.tz_italy).strftime(
                                                    "%d/%m/%Y"),
                                                viaggio.numero_passeggeri,
                                                "taxi" if viaggio.esclusivo else "collettivo")
                    riga_fattura.qta = 1
                    riga_fattura.iva = 0 if fatturazione.esente_iva else 10
                    riga_fattura.prezzo = viaggio.prezzo_netto(
                        riga_fattura.iva)

                    if viaggio.prezzo_sosta > 0:
                        # se ho una sosta, aggiungo il prezzo della sosta in fattura
                        riga_fattura.prezzo += viaggio.prezzo_sosta
                        riga_fattura.descrizione += " + sosta"

                    riga_fattura.viaggio = viaggio

                riga_fattura.fattura = fattura
                riga_fattura.save()
                riga += 10

            if fattura:
                on_fattura_end(fattura, esente_iva)
            message = "Generate %d %s." % (fatture_generate, plurale)
            messages.success(request, message)
            logAction('C', description=message, user=request.user)
            return HttpResponseRedirect(reverse("tamGenerazioneFatture"))

    return render(request,
                  template_name,
                  {
                      # riporto i valori che mi arrivano dalla selezione
                      "anno": anno,
                      "progressivo_iniziale": progressivo_iniziale,

                      "lista": lista,
                      "mediabundleJS": ('tamUI',),
                      "mediabundleCSS": ('tamUI',),
                      "singolare": nomi_fatture[tipo],
                      "fatture": fatture,
                      "plurale": plurale,
                      #								"error_message":error_message,
                      'conducenti_ricevute': conducenti_ricevute,
                      'data_generazione': data_generazione,
                      'fatturazione': fatturazione,
                      'PREZZO_VIAGGIO_NETTO': PREZZO_VIAGGIO_NETTO,
                  },
                  )
